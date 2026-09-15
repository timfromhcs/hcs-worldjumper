import os
import subprocess

def push_hf_space():
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
    
    # Configure remote
    subprocess.run(["git", "remote", "remove", "space"], capture_output=True)
    subprocess.run(["git", "remote", "add", "space", space_url], capture_output=True)
    
    print(f"Pushing commit to Hugging Face Space https://huggingface.co/spaces/{user}/{space_name}...")
    res = subprocess.run(["git", "push", "space", "main:main"], capture_output=True, text=True)
    
    if res.returncode == 0:
        print(f"SUCCESS: Deployed to Hugging Face Space https://huggingface.co/spaces/{user}/{space_name}")
        subprocess.run(["git", "remote", "remove", "space"], capture_output=True)
        return True
    else:
        err = res.stderr.replace(token, "[REDACTED_TOKEN]")
        print("HF push notice:", err)
        subprocess.run(["git", "remote", "remove", "space"], capture_output=True)
        return False

if __name__ == "__main__":
    push_hf_space()
