import os
import subprocess
import shutil

def build_windows():
    print("==========================================")
    print("Building HCS WorldJumper Windows Binary")
    print("==========================================")

    dist_dir = os.path.abspath("desktop/dist")
    build_dir = os.path.abspath("desktop/build")
    os.makedirs(dist_dir, exist_ok=True)

    import sys
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name=HCS-WorldJumper",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        "desktop/app.py"
    ]

    print(f"Running PyInstaller: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        exe_path = os.path.join(dist_dir, "HCS-WorldJumper", "HCS-WorldJumper.exe")
        print(f"SUCCESS: Windows binary built at {exe_path}")
        return exe_path
    else:
        print("PyInstaller build error:", res.stderr)
        return None

if __name__ == "__main__":
    build_windows()
