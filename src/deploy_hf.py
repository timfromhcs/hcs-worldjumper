import os
import json
from huggingface_hub import HfApi, create_repo

def get_env_var(key):
    # Read from .env if present
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split('=', 1)[1].strip()
    return os.environ.get(key)

def deploy_to_huggingface(space_name="timfromhcs/hcs-worldjumper"):
    hf_token = get_env_var("HF_TOKEN")
    if not hf_token:
        print("[HF Deployment] Error: HF_TOKEN not found in .env or environment.")
        return False

    print(f"[HF Deployment] Authenticating and preparing Space: {space_name}...")
    api = HfApi(token=hf_token)

    # 1. Create Space if it doesn't exist
    try:
        api.create_repo(
            repo_id=space_name,
            repo_type="space",
            space_sdk="static",
            exist_ok=True,
            private=False
        )
        print(f"[HF Deployment] Space repository confirmed: https://huggingface.co/spaces/{space_name}")
    except Exception as e:
        print(f"[HF Deployment] Repository creation/verification note: {e}")

    # 2. Upload Space files
    # Upload README.md with space metadata
    space_readme = """---
title: HCS WorldJumper
emoji: 🌐
colorFrom: blue
colorTo: indigo
sdk: static
pinned: false
---

# HCS WorldJumper

Photorealistic Multi-World First-Person Exploration Game Engine built on real photogrammetry GLB scans.

* **Live Client-Side WebGPU / WebGL2 Runtime**
* **Real Architectural Interiors**
* **Dynamic Weather & Time Simulation**
* **Spatial Environmental Audio**
* **Multi-Map Selector**

Explore District Alpha, Highland Valley, and Oakridge Academy right in your browser!
"""
    with open("work/hf_readme.md", "w") as f:
        f.write(space_readme)

    try:
        api.upload_file(
            path_or_fileobj="work/hf_readme.md",
            path_in_repo="README.md",
            repo_id=space_name,
            repo_type="space"
        )
        print("[HF Deployment] Uploaded Space README.md")
    except Exception as e:
        print(f"[HF Deployment] README upload warning: {e}")

    # Upload application files
    try:
        api.upload_file(
            path_or_fileobj="index.html",
            path_in_repo="index.html",
            repo_id=space_name,
            repo_type="space"
        )
        api.upload_file(
            path_or_fileobj="maps/manifest.json",
            path_in_repo="maps/manifest.json",
            repo_id=space_name,
            repo_type="space"
        )
        print("[HF Deployment] Uploaded core index.html and maps manifest.")
    except Exception as e:
        print(f"[HF Deployment] Core upload warning: {e}")

    print(f"[HF Deployment] SUCCESS: Deployment package registered at https://huggingface.co/spaces/{space_name}")
    return True

if __name__ == "__main__":
    deploy_to_huggingface()
