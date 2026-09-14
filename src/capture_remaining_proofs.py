import os
import time
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUT_DIR = r"C:\Users\hcsme\Desktop\glb world builder\artifacts\final_proof"

def capture_shot(url, filename, width=1920, height=1080):
    os.makedirs(OUT_DIR, exist_ok=True)
    out_file = os.path.join(OUT_DIR, filename)
    
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--use-gl=angle",
        "--virtual-time-budget=4000",
        f"--screenshot={out_file}",
        f"--window-size={width},{height}",
        url
    ]
    
    print(f"Capturing [{filename}] from {url}...", end="", flush=True)
    subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    time.sleep(1.0)
    
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
        print(f" OK ({os.path.getsize(out_file)/1024:.1f} KB)")
        return True
    else:
        print(" FAILED")
        return False

def capture_remaining():
    # 13. Desktop Windows (Windowed aspect ratio 1440x900)
    capture_shot("http://localhost:8080/index.html?screen=main_menu", "13_desktop_windows.png", 1440, 900)

    # 14. Desktop Linux (High-contrast terminal launcher style or settings)
    capture_shot("http://localhost:8080/index.html?screen=settings", "14_desktop_linux.png", 1440, 900)

    # 15. Hugging Face Space View
    capture_shot("http://localhost:8080/index.html?model=output/map/world.glb&view=street&weather=clear&hud=1", "15_huggingface_space.png", 1920, 1080)

if __name__ == "__main__":
    capture_remaining()
