import sys
import os
import subprocess

def main():
    # Ensure we are in root
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)

    # Add src to python path for the subprocess
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(root, "src") + os.pathsep + env.get("PYTHONPATH", "")

    print("Launching Cognitive Interface...")
    try:
        cmd = [sys.executable, "-m", "streamlit", "run", "src/remember_me/ui/streamlit_app.py"]
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\nShutdown.")

if __name__ == "__main__":
    main()
