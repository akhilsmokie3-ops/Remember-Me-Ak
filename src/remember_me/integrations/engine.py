import os
import requests
import torch
from threading import Thread

# Lazy imports for heavy libs
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class LlamaCppClient:
    """Client for local llama-server (OpenAI Compatible)."""
    def __init__(self, base_url="http://localhost:8081"):
        self.base_url = base_url

    def ping(self):
        try:
            # Simple check, /health or just root
            requests.get(f"{self.base_url}/health", timeout=1)
            return True
        except:
            return False

    def generate(self, messages, max_tokens=512, temperature=0.7):
        try:
            url = f"{self.base_url}/v1/chat/completions"
            payload = {
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            res = requests.post(url, json=payload, timeout=120)
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            return f"Error: Server returned {res.status_code} - {res.text}"
        except Exception as e:
            return f"Error connecting to brain: {e}"

class ModelRegistry:
    """
    Manages local AI models.
    Supports both:
    1. Local Llama Server (Preferred, via LlamaCppClient)
    2. In-Process Transformers (Fallback)
    """

    MODELS = {
        "tiny": {
            "id": "Qwen/Qwen2.5-0.5B-Instruct",
            "name": "Qwen 2.5 (0.5B) - Tiny",
            "description": "Ultra-fast, low memory (Run anywhere)"
        },
        "small": {
            "id": "Qwen/Qwen2.5-1.5B-Instruct",
            "name": "Qwen 2.5 (1.5B) - Small",
            "description": "Balanced speed/intelligence (Recommended)"
        },
        "medium": {
            "id": "HuggingFaceTB/SmolLM2-1.7B-Instruct",
            "name": "SmolLM2 (1.7B) - Medium",
            "description": "High reasoning capability"
        }
    }

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.client = LlamaCppClient()
        self.use_remote = False
        self.current_model = None
        self.tokenizer = None
        self.model_id = None

        # Check if remote is alive
        if self.client.ping():
            print("✓ Detected Active Llama Server. Using Remote Engine.")
            self.use_remote = True
            self.model_id = "remote-llama"
        else:
            print("⚠ No Llama Server detected. Engine is in Standby (Transformers).")
            self.use_remote = False

    def list_models(self):
        return self.MODELS

    def load_model(self, key: str):
        """
        Downloads and loads the specified model key (Transformers mode).
        """
        if self.use_remote:
            print(f"⚠ Remote server active. Ignoring local load for '{key}'.")
            return True

        if not TRANSFORMERS_AVAILABLE:
            print("❌ Transformers library not installed. Cannot load local model.")
            return False

        if key not in self.MODELS:
            raise ValueError(f"Unknown model key: {key}")

        info = self.MODELS[key]
        print(f"Loading {info['name']} on {self.device}...")

        try:
            self.tokenizer = AutoTokenizer.from_pretrained(info["id"])
            self.current_model = AutoModelForCausalLM.from_pretrained(
                info["id"],
                dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
                low_cpu_mem_usage=True
            )
            if self.device == "cpu":
                self.current_model.to("cpu")

            self.model_id = key
            print(f"✓ {info['name']} loaded successfully.")
            return True
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            return False

    def generate_response(self, user_input: str, context_str: str, system_prompt: str = None) -> str:
        """
        Generates a response using the active engine.
        """
        # Construct Prompt with SELF-AWARENESS Injection
        default_system = (
            "You are a helpful AI assistant equipped with the Remember Me Cognitive Kernel. "
            "You have long-term memory via CSNP, and access to tools like Image Generation and Web Search. "
            "Do not deny these capabilities. If the user refers to past conversations, assume your memory context is accurate. "
            "Answer directly and helpfully."
        )
        sys_p = system_prompt if system_prompt else default_system

        # Combine context with user input
        full_context = ""
        if context_str:
            full_context = f"\n[RELEVANT LONG-TERM MEMORY]:\n{context_str}\n"

        messages = [
            {"role": "system", "content": sys_p},
            {"role": "user", "content": f"{full_context}\nUSER: {user_input}"}
        ]

        # 1. Remote Path
        if self.use_remote:
            return self.client.generate(messages)

        # 2. Local Transformers Path
        if not self.current_model:
            return "Error: No model loaded. Use /model to select one."

        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        # Generate
        with torch.no_grad():
            generated_ids = self.current_model.generate(
                inputs.input_ids,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.7,
                top_p=0.9
            )

        # Decode
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(inputs.input_ids, generated_ids)
        ]
        response = self.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        return response

    def generate_stream(self, user_input: str, context_str: str):
        """
        Generator for streaming response.
        """
        # TODO: Implement streaming for remote client
        if self.use_remote:
            yield self.generate_response(user_input, context_str)
            return

        if not self.current_model:
            yield "Error: No model loaded."
            return

        full_context = ""
        if context_str:
            full_context = f"\n[RELEVANT LONG-TERM MEMORY]:\n{context_str}\n"

        system_prompt = (
            "You are a helpful AI assistant equipped with the Remember Me Cognitive Kernel. "
            "You have long-term memory via CSNP. Use the provided memory context to answer questions about the past."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{full_context}\nUSER: {user_input}"}
        ]

        text = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer([text], return_tensors="pt").to(self.device)

        streamer = TextIteratorStreamer(self.tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = dict(
            inputs,
            streamer=streamer,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.7
        )

        thread = Thread(target=self.current_model.generate, kwargs=generation_kwargs)
        thread.start()

        for new_text in streamer:
            yield new_text
