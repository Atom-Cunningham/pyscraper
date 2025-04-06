import os
import json
import subprocess
import sys

def main():
    # file containing repos, with clone_url attributes
    json_file = sys.argv[1]
    # rust binary
    rust_binary = os.path.join(os.getcwd(), "rust_ffi_metrics","target", "release","rust_ffi_metrics.exe")

    
    workspace = os.path.join(os.getcwd(), "rust_clones")

    analyze_json_repos(json_file, rust_binary, workspace, max_count=1)

def clone_repo(clone_url, target_dir):
    if os.path.exists(target_dir):
        print(f"[+] Repo already cloned: {target_dir}")
        return True
    try:
        subprocess.run(["git", "clone", "--depth=1", clone_url, target_dir], check=True)
        print(f"[+] Cloned: {clone_url}")
        return True
    except subprocess.CalledProcessError:
        print(f"[!] Failed to clone: {clone_url}")
        return False

def analyze_repo(path, rust_binary):
    try:
        output = subprocess.check_output([rust_binary, path], stderr=subprocess.DEVNULL)
        lines = output.decode().strip().splitlines()
        return {
            "extern_c": int(lines[0].split(":")[1]),
            "link_attrs": int(lines[1].split(":")[1]),
            "no_mangle": int(lines[2].split(":")[1]),
        }
    except Exception as e:
        print(f"[!] Analysis failed at {path}: {e}")
        return None

def analyze_json_repos(json_file, rust_binary, workspace, max_repo_size = 100, output_file = "ffi_metrics_sample.json", max_count=10, delete_after=False):
    os.makedirs(workspace, exist_ok=True)
    
    with open(json_file, "r", encoding="utf-8") as f:
        repos = json.load(f)

    count = 0
    results = {}
    for name, info in repos.items():
        if info[".rs"] <= 0:
            continue
        if info["total"] > max_repo_size:
            continue
        if count > max_count:
            break
        
        clone_url = info["clone_url"]
        local_path = os.path.join(workspace, name.replace("/", "_"))  # Avoid nesting dirs
        
        if clone_repo(clone_url, local_path):
            metrics = analyze_repo(local_path, rust_binary)
            if metrics:
                results[name] = metrics

            if delete_after:
                subprocess.run(["rm", "-rf", local_path])

        #Testing
        print(f"[~] Expecting repo at: {local_path}")
        if not os.path.exists(local_path):
            print(f"[!] Repo path does not exist after clone: {local_path}")
        
        count += 1

    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2)

    print(f"✅ Done analyzing {count} repositories.")

main()