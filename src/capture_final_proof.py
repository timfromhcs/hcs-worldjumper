import os
import time
import subprocess

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE_URL = "http://localhost:8080/index.html"
OUT_DIR = r"C:\Users\hcsme\Desktop\glb world builder\artifacts\final_proof"

def capture_shot(query_param, filename, timeout=30):
    os.makedirs(OUT_DIR, exist_ok=True)
    out_file = os.path.join(OUT_DIR, filename)
    url = f"{BASE_URL}{query_param}"
    
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--no-sandbox",
        "--use-gl=angle",
        "--virtual-time-budget=5000",
        f"--screenshot={out_file}",
        "--window-size=1920,1080",
        url
    ]
    
    print(f"Capturing [{filename}] from {url}...", end="", flush=True)
    subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    time.sleep(1.0)
    
    if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
        print(f" OK ({os.path.getsize(out_file)/1024:.1f} KB)")
        return True
    else:
        print(" FAILED")
        return False

def capture_all_final_proofs():
    proofs = [
        ("?screen=main_menu", "01_main_menu.png"),
        ("?screen=world_selector", "02_world_selector.png"),
        ("?model=output/map/world.glb&view=street&weather=clear&hud=1", "03_map1_pov.png"),
        ("?model=output/map2/world.glb&view=street&weather=golden&hud=1", "04_map2_pov.png"),
        ("?model=output/schoolmap/world.glb&view=street&weather=overcast&hud=1", "05_schoolmap_pov.png"),
        ("?model=output/map/world.glb&view=interior&weather=clear&hud=1", "06_interior.png"),
        ("?model=output/map/world.glb&view=vegetation&weather=clear&hud=1", "07_vegetation.png"),
        ("?model=output/map/world.glb&view=street&weather=rain&hud=1", "08_rain.png"),
        ("?model=output/map/world.glb&view=street&weather=night&hud=1", "09_night.png"),
        ("?model=output/map/world.glb&view=street&debug=1", "10_audio_runtime.png"),
        ("?model=output/map/world.glb&view=street&debug=1", "11_webgpu_runtime.png"),
        ("?screen=settings", "12_settings.png"),
    ]

    for q, f in proofs:
        capture_shot(q, f)

if __name__ == "__main__":
    capture_all_final_proofs()
