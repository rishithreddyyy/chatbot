"""
Main entry point for the Multi-Agent Coding Assistant.
Run with:
    python main.py          # Launches Streamlit Web UI
    python main.py --cli    # Launches interactive Terminal CLI
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    args = sys.argv[1:]
    if "--cli" in args:
        import cli
        cli.main()
    else:
        app_file = BASE_DIR / "app.py"
        print(f"Launching Multi-Agent Coding Assistant Web App via Streamlit...")
        subprocess.run(["streamlit", "run", str(app_file)])

if __name__ == "__main__":
    main()

