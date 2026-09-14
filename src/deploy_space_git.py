import os
import shutil
import subprocess

def deploy():
    env = {}
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    env[k] = v
                    
    token = env.get("HF_TOKEN")
    user = env.get("GITHUB_USERNAME", "timfromhcs")
    space_name = "hcs-worldjumper"
    
    hf_dir = os.path.abspath("work/hf_deploy")
    if os.path.exists(hf_dir):
        shutil.rmtree(hf_dir)
    os.makedirs(hf_dir, exist_ok=True)
    
    # 1. Write Space README
    readme_content = """---
title: HCS WorldJumper
emoji: 🌐
colorFrom: blue
colorTo: indigo
sdk: static
pinned: false
---

# HCS WorldJumper

Photorealistic Multi-World Exploration Engine with WebGPU, Architectural Interiors, Weather, and Spatial Audio.
"""
    with open(os.path.join(hf_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    # 2. Copy index.html, maps, src/runtime
    shutil.copy("index.html", os.path.join(hf_dir, "index.html"))
    shutil.copytree("src/runtime", os.path.join(hf_dir, "src/runtime"))
    shutil.copytree("maps", os.path.join(hf_dir, "maps"))
    
    # 3. Init git in hf_dir
    subprocess.run(["git", "init"], cwd=hf_dir, capture_output=True)
    subprocess.run(["git", "config", "user.name", "timfromhcs"], cwd=hf_dir, capture_output=True)
    subprocess.run(["git", "config", "user.email", "timfromhcs@users.noreply.github.com"], cwd=hf_dir, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=hf_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "Deploy HCS WorldJumper Space"], cwd=hf_dir, capture_output=True)
    
    # Push to HF Space
    space_url = f"https://{user}:{token}@huggingface.co/spaces/{user}/{space_name}"
    print(f"Deploying to Hugging Face Space: https://huggingface.co/spaces/{user}/{space_name}...")
    res = subprocess.run(["git", "push", space_url, "master:main", "--force"], cwd=hf_dir, capture_output=True, text=True)
    
    if res.returncode == 0:
        print("SUCCESS: Hugging Face Space deployed and active!")
        return True
    else:
        err = res.stderr.replace(token, "[REDACTED_TOKEN]")
        print("HF Space deploy status:", err)
        return False

if __name__ == "__main__":
    deploy()
