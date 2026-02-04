import torch

# Lazy load heavy dependencies
_diffusers_imported = False
_pyttsx3_imported = False
_ddgs_imported = False

AutoPipelineForText2Image = None
pyttsx3 = None
DDGS = None

def _import_diffusers():
    global _diffusers_imported, AutoPipelineForText2Image
    if not _diffusers_imported:
        try:
            from diffusers import AutoPipelineForText2Image as APT2I
            AutoPipelineForText2Image = APT2I
            _diffusers_imported = True
        except ImportError:
            print("❌ diffusers not found. Install with `pip install diffusers`")

def _import_pyttsx3():
    global _pyttsx3_imported, pyttsx3
    if not _pyttsx3_imported:
        try:
            import pyttsx3 as p3
            pyttsx3 = p3
            _pyttsx3_imported = True
        except ImportError:
            print("❌ pyttsx3 not found. Install with `pip install pyttsx3`")

def _import_ddgs():
    global _ddgs_imported, DDGS
    if not _ddgs_imported:
        try:
            from duckduckgo_search import DDGS as D
            DDGS = D
            _ddgs_imported = True
        except ImportError:
            print("❌ duckduckgo_search not found. Install with `pip install duckduckgo-search`")


class ToolArsenal:
    """
    Collection of tools for the AI agent:
    - Web Search (DuckDuckGo)
    - Image Generation (Diffusers)
    - Text-to-Speech (pyttsx3)
    """

    def __init__(self):
        # ⚡ Bolt: Lazy load DDGS to avoid network/session overhead at startup
        self.ddgs = None
        self.image_pipe = None
        self.tts_engine = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def web_search(self, query: str, max_results=3) -> str:
        """
        Performs a web search using DuckDuckGo.
        """
        _import_ddgs()
        if not _ddgs_imported:
            return "Web Search unavailable."

        if self.ddgs is None:
            try:
                self.ddgs = DDGS()
            except Exception as e:
                return f"Failed to initialize Search: {e}"

        try:
            results = self.ddgs.text(query, max_results=max_results)
            if not results:
                return "No results found."

            summary = []
            for r in results:
                summary.append(f"- {r['title']}: {r['body']}")

            return "\n".join(summary)
        except Exception as e:
            # Fallback for network restrictions
            return f"Search Error (Network may be restricted): {e}"

    def generate_image(self, prompt: str, output_path: str = "output.png") -> str:
        """
        Generates an image from text using Stable Diffusion (Latent Consistency Model if avail, or standard SD).
        Downloads model on first use.
        """
        _import_diffusers()
        if not _diffusers_imported:
            return "Image Generation unavailable."

        if self.image_pipe is None:
            print("⏳ Loading Image Generation Model (this may take a while first time)...")
            try:
                # Use a fast, small model.
                # 'stabilityai/sd-turbo' is great but big.
                model_id = "stabilityai/sd-turbo"

                # Note: `from_pretrained` arguments depend on the pipeline class.
                # AutoPipelineForText2Image handles most, but we should be careful with `dtype` vs `torch_dtype`
                # Recent diffusers use `torch_dtype`.

                self.image_pipe = AutoPipelineForText2Image.from_pretrained(
                    model_id,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    variant="fp16" if self.device == "cuda" else None
                )
                self.image_pipe.to(self.device)
            except Exception as e:
                return f"Failed to load Image Model: {e}"

        print(f"🎨 Generating image for: '{prompt}'...")
        try:
            # SD-Turbo needs only 1-4 steps
            image = self.image_pipe(prompt=prompt, num_inference_steps=1, guidance_scale=0.0).images[0]
            image.save(output_path)
            return f"Image saved to {output_path}"
        except Exception as e:
            return f"Generation failed: {e}"

    def speak(self, text: str):
        """
        Speaks the text using local TTS.
        """
        _import_pyttsx3()
        if not _pyttsx3_imported:
            return

        try:
            if self.tts_engine is None:
                self.tts_engine = pyttsx3.init()
                # Set properties (optional)
                self.tts_engine.setProperty('rate', 150)

            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            # Often fails in headless environments (no audio device)
            print(f"[Audio Device Error: {e}]")
            # We swallow the error so the app doesn't crash
