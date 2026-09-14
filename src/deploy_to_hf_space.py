import os
import shutil
import subprocess
import time
import urllib.request
import json

def deploy():
    print("=== HCS WORLDJUMPER: HUGGING FACE SPACE DEPLOYMENT ===")
    
    # 1. Load credentials
    token = os.getenv("HF_TOKEN")
    if not token and os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("HF_TOKEN="):
                    token = line.strip().split("=", 1)[1].strip()
                    break
                    
    if not token:
        raise RuntimeError("HF_TOKEN not found in environment or .env!")
        
    user = "timfromhcs"
    space_name = "hcs-worldjumper"
    space_repo_url = f"https://{user}:{token}@huggingface.co/spaces/{user}/{space_name}"
    
    # 2. Verify dist directory exists and contains index.html
    if not os.path.exists("dist/index.html"):
        print("Building production static bundle with vite build...")
        subprocess.run(["npm", "run", "build"], check=True)
        
    def handle_remove_readonly(func, path, exc):
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)

    hf_dir = os.path.abspath("work/hf_deploy")
    if os.path.exists(hf_dir):
        try:
            shutil.rmtree(hf_dir, onexc=handle_remove_readonly)
        except Exception:
            subprocess.run(["cmd", "/c", "rd", "/s", "/q", hf_dir], capture_output=True)
    os.makedirs(hf_dir, exist_ok=True)
    
    # 3. Create Space README with exact static configuration
    readme_content = """---
title: HCS WorldJumper
emoji: 🌐
colorFrom: blue
colorTo: indigo
sdk: static
app_file: dist/index.html
pinned: false
---

# HCS WorldJumper

Photorealistic Multi-World Exploration Engine with Three.js WebGPU / WebGL2, Procedural PBR, AI Architectural Reconstruction, Dynamic Weather, and Spatial Audio.

## Live Controls
- **W / A / S / D**: First-person locomotion
- **Mouse**: Look / Aim / Heading
- **Space**: Jump
- **C**: Crouch
- **Shift**: Sprint
- **F3**: Engine profiler & diagnostics overlay
- **ESC**: System menu / Map selector
"""
    with open(os.path.join(hf_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    # 4. Copy dist folder and prune non-runtime files
    print("Copying built production bundle to staging area...")
    shutil.copytree("dist", os.path.join(hf_dir, "dist"))
    
    # Prune heavy test proof screenshots not needed by web runtime
    proof_dir = os.path.join(hf_dir, "dist", "artifacts", "proof")
    if os.path.exists(proof_dir):
        shutil.rmtree(proof_dir)
    final_proof_dir = os.path.join(hf_dir, "dist", "artifacts", "final_proof")
    if os.path.exists(final_proof_dir):
        shutil.rmtree(final_proof_dir)
    deploy_art_dir = os.path.join(hf_dir, "dist", "artifacts", "deployment")
    if os.path.exists(deploy_art_dir):
        shutil.rmtree(deploy_art_dir)
    
    # Also copy package files and source files
    shutil.copy("package.json", os.path.join(hf_dir, "package.json"))
    shutil.copy("package-lock.json", os.path.join(hf_dir, "package-lock.json"))
    shutil.copy("vite.config.js", os.path.join(hf_dir, "vite.config.js"))
    shutil.copy("index.html", os.path.join(hf_dir, "index.html"))
    shutil.copytree("src", os.path.join(hf_dir, "src"))
    
    # 5. Initialize git and configure Git LFS for ALL binary formats
    print("Configuring git and Git LFS for binary assets (*.glb, *.png, *.wav)...")
    subprocess.run(["git", "init"], cwd=hf_dir, check=True)
    subprocess.run(["git", "config", "user.name", "timfromhcs"], cwd=hf_dir, check=True)
    subprocess.run(["git", "config", "user.email", "timfromhcs@users.noreply.github.com"], cwd=hf_dir, check=True)
    
    # Setup LFS for all binary types
    subprocess.run(["git", "lfs", "install"], cwd=hf_dir, check=True)
    for pattern in ["*.glb", "*.png", "*.wav", "*.jpg", "*.mp3"]:
        subprocess.run(["git", "lfs", "track", pattern], cwd=hf_dir, check=True)
    subprocess.run(["git", "add", ".gitattributes"], cwd=hf_dir, check=True)
    
    # Add all files
    print("Staging deployment files...")
    subprocess.run(["git", "add", "."], cwd=hf_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Deploy verified HCS WorldJumper production static bundle"], cwd=hf_dir, check=True)
    
    # Push to Hugging Face
    print(f"Pushing to Hugging Face Space: https://huggingface.co/spaces/{user}/{space_name}...")
    res = subprocess.run(
        ["git", "push", space_repo_url, "master:main", "--force"],
        cwd=hf_dir,
        capture_output=True,
        text=True
    )
    
    if res.returncode == 0:
        print("\n=== SUCCESS: Hugging Face Space deployed successfully! ===")
        print(f"Space URL: https://huggingface.co/spaces/{user}/{space_name}")
        print(f"Direct Static App URL: https://{user}-{space_name}.hf.space/")
        return True
    else:
        sanitized_err = res.stderr.replace(token, "[REDACTED_TOKEN]")
        print("Git push error:\n", sanitized_err)
        return False

if __name__ == "__main__":
    deploy()
