import os
import subprocess

def push_github():
    env = {}
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if '=' in line:
                    k, v = line.strip().split('=', 1)
                    env[k] = v
                    
    token = env.get("GITHUB_TOKEN")
    user = env.get("GITHUB_USERNAME", "timfromhcs")
    
    if not token:
        print("Error: GITHUB_TOKEN not found.")
        return False
        
    repo_url = f"https://{user}:{token}@github.com/{user}/hcs-worldjumper.git"
    
    # Configure remote
    subprocess.run(["git", "remote", "remove", "origin"], capture_output=True)
    add_rem = subprocess.run(["git", "remote", "add", "origin", repo_url], capture_output=True)
    subprocess.run(["git", "branch", "-M", "main"], capture_output=True)
    
    print("Pushing commit to GitHub repository https://github.com/timfromhcs/hcs-worldjumper...")
    res = subprocess.run(["git", "push", "-u", "origin", "main", "--force"], capture_output=True, text=True)
    
    if res.returncode == 0:
        print("SUCCESS: Code pushed to https://github.com/timfromhcs/hcs-worldjumper")
        # Remove token from remote url after push to keep local git remote clean
        subprocess.run(["git", "remote", "set-url", "origin", f"https://github.com/{user}/hcs-worldjumper.git"], capture_output=True)
        return True
    else:
        # Sanitize token from output if error
        err = res.stderr.replace(token, "[REDACTED_TOKEN]")
        print("Push error:", err)
        subprocess.run(["git", "remote", "set-url", "origin", f"https://github.com/{user}/hcs-worldjumper.git"], capture_output=True)
        return False

if __name__ == "__main__":
    push_github()
