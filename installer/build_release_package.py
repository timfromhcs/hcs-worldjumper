import os
import shutil
import hashlib
import zipfile
import tarfile

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(4096 * 1024):
            h.update(chunk)
    return h.hexdigest()

def build_releases():
    os.makedirs("installer", exist_ok=True)
    
    # 1. Windows Release Zip
    win_src = "desktop/dist/HCS-WorldJumper"
    win_zip = "installer/HCS-WorldJumper-v1.0.0-windows-x64.zip"
    if os.path.exists(win_src):
        print(f"Archiving Windows release to {win_zip}...")
        with zipfile.ZipFile(win_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(win_src):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, win_src)
                    zf.write(full_path, arcname=os.path.join("HCS-WorldJumper", rel_path))
        print(f"Windows release built: {os.path.getsize(win_zip)/(1024*1024):.2f} MB")

    # 2. Linux Release Tarball
    linux_tar = "installer/HCS-WorldJumper-v1.0.0-linux-x86_64.tar.gz"
    print(f"Archiving Linux release to {linux_tar}...")
    with tarfile.open(linux_tar, "w:gz") as tar:
        tar.add("desktop/HCS-WorldJumper-linux.sh", arcname="HCS-WorldJumper/HCS-WorldJumper-linux.sh")
        tar.add("desktop/app.py", arcname="HCS-WorldJumper/app.py")
        tar.add("index.html", arcname="HCS-WorldJumper/index.html")
        tar.add("maps/manifest.json", arcname="HCS-WorldJumper/maps/manifest.json")
    print(f"Linux release built: {os.path.getsize(linux_tar)/(1024*1024):.2f} MB")

    # 3. SHA256SUMS.txt
    sums_file = "installer/SHA256SUMS.txt"
    with open(sums_file, "w") as f:
        for p in [win_zip, linux_tar]:
            if os.path.exists(p):
                digest = sha256_file(p)
                f.write(f"{digest}  {os.path.basename(p)}\n")
                print(f"SHA-256 [{os.path.basename(p)}]: {digest}")

    print("Release packages and SHA256SUMS.txt generated successfully.")

if __name__ == "__main__":
    build_releases()
