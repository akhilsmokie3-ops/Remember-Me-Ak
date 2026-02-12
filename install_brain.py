import os
import requests
import sys
import subprocess
import time

BRAIN_DIR = os.path.abspath("src/remember_me/brain_engine")
MODEL_PATH = os.path.join(BRAIN_DIR, "model.gguf")
# DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf (4.9 GB)
# DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf (~5 GB)
# Source: bartowski (Reliable GGUF Quantizer)
MODEL_URL = "https://huggingface.co/bartowski/DeepSeek-R1-Distill-Llama-8B-GGUF/resolve/main/DeepSeek-R1-Distill-Llama-8B-Q4_K_M.gguf"

def install_dependency(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def check_dependencies():
    print("[*] Verifying Subsystems...")
    try:
        import tqdm
    except ImportError:
        print("[!] TQDM missing. Installing...")
        install_dependency("tqdm")
    
    try:
        import requests
        import streamlit
        import bs4
    except ImportError:
        print("[!] Core libs missing. Installing requirements...")
        if os.path.exists("requirements.txt"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            # Emergency fallback dependency list
            deps = ["requests", "streamlit", "beautifulsoup4", "tqdm"]
            for d in deps: install_dependency(d)

def download_brain():
    if not os.path.exists(BRAIN_DIR):
        os.makedirs(BRAIN_DIR)

    # Logic: If model missing OR model is tiny (<1GB, meaning it's the 0.5B toy or a 404 error page), download the Beast.
    should_download = False
    if not os.path.exists(MODEL_PATH):
        print("[!] No Brain Detected.")
        should_download = True
    else:
        size_gb = os.path.getsize(MODEL_PATH) / (1024 * 1024 * 1024)
        if size_gb < 2.0:
            print(f"[!] Brain file corrupted or too small ({size_gb:.2f} GB). Re-acquiring DeepSeek R1...")
            should_download = True
        else:
            print(f"[*] Brain Active: {size_gb:.2f} GB. Systems Green.")
    
    if should_download:
        print(f"[*] Initializing Download Protocol: DeepSeek-R1-Distill-Llama-8B")
        print(f"[*] Source: {MODEL_URL}")
        print(f"[*] Target Vector: {MODEL_PATH}")

        # Nuke verify if exists to prevent lock issues
        if os.path.exists(MODEL_PATH):
            try:
                os.remove(MODEL_PATH)
            except:
                pass

        try:
            from tqdm import tqdm
            # STREAM is critical here, but so is checking the status code.
            response = requests.get(MODEL_URL, stream=True, allow_redirects=True)
            response.raise_for_status() # Check for 404/500 errors immediately

            total_size = int(response.headers.get('content-length', 0))
            if total_size < 100000000: # If less than 100MB, it's NOT the model.
                raise ValueError(f"Download size too small ({total_size} bytes). Likely an HTML page or API error.")

            block_size = 1024 * 1024 # 1 MB chunk size for faster disk IO
            
            with open(MODEL_PATH, 'wb') as file, tqdm(
                desc="Downloading Brain",
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(block_size):
                    bar.update(len(data))
                    file.write(data)
            print("\n[+] Brain Acquired. Intelligence Online.")
        except Exception as e:
            print(f"\n[!] CRITICAL FAILURE: {e}")
            input("Press Enter to Exit...")
            sys.exit(1)

if __name__ == "__main__":
    print("\n-------------------------------------------")
    print(" SOVEREIGN BOOTLOADER v2.2 ")
    print("-------------------------------------------\n")
    check_dependencies()
    download_brain()
    print("\n[*] Boot Sequence Complete.")
    time.sleep(1)
