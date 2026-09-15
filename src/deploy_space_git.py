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
    
    if not token:
        print("Error: HF_TOKEN not found.")
        return False
        
    space_url = f"https://{user}:{token}@huggingface.co/spaces/{user}/{space_name}"
    clone_dir = os.path.abspath("work/hf_space_repo")
    
    def _remove_readonly(func, path, excinfo):
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)

    if os.path.exists(clone_dir):
        shutil.rmtree(clone_dir, onerror=_remove_readonly)
        
    print(f"Cloning Hugging Face Space repository...")
    res = subprocess.run(["git", "clone", space_url, clone_dir], capture_output=True, text=True)
    if res.returncode != 0:
        err = res.stderr.replace(token, "[REDACTED_TOKEN]")
        print("Clone failed:", err)
        return False
        
    # Set user info
    subprocess.run(["git", "config", "user.name", "timfromhcs"], cwd=clone_dir, capture_output=True)
    subprocess.run(["git", "config", "user.email", "timfromhcs@users.noreply.github.com"], cwd=clone_dir, capture_output=True)
    
    # 1. Update README.md with app_file: index.html
    readme_content = """---
title: HCS WorldJumper
emoji: 🌐
colorFrom: blue
colorTo: indigo
sdk: static
app_file: index.html
pinned: false
---

# HCS WorldJumper

Photorealistic Multi-World Exploration Engine with WebGPU, Cloud-First Reconstructed Architecture, Weather, and Spatial Audio.
"""
    with open(os.path.join(clone_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
        
    # 2. Update .gitattributes with complete LFS coverage
    gitattr_content = """*.glb filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.wasm filter=lfs diff=lfs merge=lfs -text
"""
    with open(os.path.join(clone_dir, ".gitattributes"), "w", encoding="utf-8") as f:
        f.write(gitattr_content)

    # 3. Copy index.html, adjusting importmap for static cloud CDN
    with open("index.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    cdn_importmap = """  <script type="importmap">
  {
    "imports": {
      "three": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js",
      "three/webgpu": "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.webgpu.js",
      "three/examples/jsm/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/",
      "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/"
    }
  }
  </script>"""
    
    import re
    html_cdn = re.sub(r'<script type="importmap">.*?</script>', cdn_importmap, html, flags=re.DOTALL)
    with open(os.path.join(clone_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_cdn)
    
    # Copy Runtime scripts
    runtime_dst = os.path.join(clone_dir, "src", "runtime")
    if os.path.exists(runtime_dst):
        shutil.rmtree(runtime_dst)
    os.makedirs(os.path.dirname(runtime_dst), exist_ok=True)
    shutil.copytree("src/runtime", runtime_dst)
    
    # Copy Viewer with CDN importmap
    viewer_dst = os.path.join(clone_dir, "viewer")
    if os.path.exists(viewer_dst):
        shutil.rmtree(viewer_dst)
    shutil.copytree("viewer", viewer_dst)
    viewer_html_path = os.path.join(viewer_dst, "index.html")
    if os.path.exists(viewer_html_path):
        with open(viewer_html_path, "r", encoding="utf-8") as vf:
            v_html = vf.read()
        v_html_cdn = re.sub(r'<script type="importmap">.*?</script>', cdn_importmap, v_html, flags=re.DOTALL)
        with open(viewer_html_path, "w", encoding="utf-8") as vf:
            vf.write(v_html_cdn)
    
    # Output assets (world.glb, physics, manifests)
    for m in ["map", "map2", "schoolmap"]:
        out_m_dst = os.path.join(clone_dir, "output", m)
        os.makedirs(out_m_dst, exist_ok=True)
        # copy world.glb
        shutil.copy2(f"output/{m}/world.glb", os.path.join(out_m_dst, "world.glb"))
        # copy physics
        phys_dst = os.path.join(out_m_dst, "physics")
        os.makedirs(phys_dst, exist_ok=True)
        shutil.copy2(f"output/{m}/physics/physics.json", os.path.join(phys_dst, "physics.json"))
        # copy manifest
        if os.path.exists(f"output/{m}/manifest.json"):
            shutil.copy2(f"output/{m}/manifest.json", os.path.join(out_m_dst, "manifest.json"))
            
    # Public output sync
    pub_dst = os.path.join(clone_dir, "public", "output")
    if os.path.exists("public/output"):
        if os.path.exists(pub_dst):
            shutil.rmtree(pub_dst)
        os.makedirs(os.path.dirname(pub_dst), exist_ok=True)
        shutil.copytree("public/output", pub_dst)
        
    # Audio assets
    assets_audio_dst = os.path.join(clone_dir, "assets", "audio")
    if os.path.exists("assets/audio"):
        os.makedirs(assets_audio_dst, exist_ok=True)
        for wav_file in os.listdir("assets/audio"):
            if wav_file.endswith((".wav", ".mp3")):
                shutil.copy2(os.path.join("assets/audio", wav_file), os.path.join(assets_audio_dst, wav_file))
                
    # 4. Remove any node_modules if present in clone
    old_nm = os.path.join(clone_dir, "node_modules")
    if os.path.exists(old_nm):
        shutil.rmtree(old_nm, ignore_errors=True)
        
    # 5. Commit and Push
    print(f"Staging and committing production assets...")
    subprocess.run(["git", "add", "-A"], cwd=clone_dir, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: deploy reconstructed PBR worlds and updated physics"], cwd=clone_dir, capture_output=True)
    
    print(f"Pushing linear update to Hugging Face Space...")
    res_push = subprocess.run(["git", "push", "origin", "main"], cwd=clone_dir, capture_output=True, text=True)
    
    if res_push.returncode == 0:
        print(f"SUCCESS: Deployed to Hugging Face Space https://huggingface.co/spaces/{user}/{space_name}")
        shutil.rmtree(clone_dir, onerror=_remove_readonly)
        return True
    else:
        err = res_push.stderr.replace(token, "[REDACTED_TOKEN]")
        print("HF Space deploy notice:", err)
        shutil.rmtree(clone_dir, onerror=_remove_readonly)
        return False

if __name__ == "__main__":
    deploy()
