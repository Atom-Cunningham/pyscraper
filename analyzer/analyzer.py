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

    analyze_json_repos(json_file, rust_binary, workspace, max_repo_size = 100000, max_count=500, delete_after=True)

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

def clone_repo_sparse(clone_url, target_dir, rs_paths=None):
    if os.path.exists(target_dir):
        print(f"[+] Repo already cloned: {target_dir}")
        return True
    try:
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", clone_url, target_dir], check=True)
        print(f"[+] Cloned (sparse): {clone_url}")
        if rs_paths:
            os.chdir(target_dir)
            subprocess.run(["git", "sparse-checkout", "init", "--cone"], check=True)
            subprocess.run(["git", "sparse-checkout", "set"] + rs_paths, check=True)
            subprocess.run(["git", "checkout"], check=True)
            os.chdir("..")
        return True
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"[!] Failed to clone: {clone_url}")
        return False

def get_rs_paths(filepath):
    #path to rs_paths/git_file_path.rs
    
    print(f"rs_path_file: {filepath}")
    if not filepath or not os.path.exists(filepath):
        print(f"could not find filepath{filepath}")
        return None  # No sparse paths available

    with open(filepath, "r") as f:
        paths = [line.strip() for line in f if line.strip()]
        return paths
    return None

def analyze_repo(path, rust_binary):
    try:
        output = subprocess.check_output([rust_binary, path], stderr=subprocess.DEVNULL)
        lines = output.decode().strip().splitlines()
        print(lines)
        return {
            "total_lines": int(lines[0].split(":")[1]),
            "extern_c": int(lines[1].split(":")[1]),
            "link_attrs": int(lines[2].split(":")[1]),
            "no_mangle": int(lines[3].split(":")[1]),
            "syntax_tree_height": int(lines[4].split(":")[1]),
        }
    except Exception as e:
        print(f"[!] Analysis failed at {path}: {e}")
        return None
    
def categorize_usage(rs_paths):
    categories = {"kernel": 0, "driver": 0, "sandbox": 0, "library": 0, "other": 0}
    for path in rs_paths:
        if "kernel" in path:
            categories["kernel"] += 1
        elif "driver" in path:
            categories["driver"] += 1
        elif "sandbox" in path:
            categories["sandbox"] += 1
        elif "lib" in path:
            categories["library"] += 1
        else:
            categories["other"] += 1
    return categories

def average_file_depth(rs_paths):
    depths = [path.count("/") for path in rs_paths]
    return sum(depths) / len(depths) if depths else 0

def analyze_json_repos(json_file, rust_binary, workspace, max_repo_size = 100, output_file = "ffi_metrics_sample1.json", max_count=10, delete_after=False):
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

        # if in rust_clones, cd rs_paths
        rs_path_file = info["rs_path_file"]
        currdirectory = os.getcwd()
        while not currdirectory.endswith("analyzer"):
            os.chdir("..")
            currdirectory = os.getcwd()
        rs_path_file = os.path.join(currdirectory, rs_path_file)
        # get list of rs files in repository:
        rs_paths = get_rs_paths(rs_path_file)

        if rs_paths == None:
            continue
        
        
        local_path = os.path.join(workspace, name.replace("/", "_"))  # Avoid nesting dirs
        if clone_repo_sparse(clone_url, local_path, rs_paths):
            metrics = analyze_repo(local_path, rust_binary)
            if metrics:
                metrics["usage"] = categorize_usage(rs_paths)
                metrics["average_file_depth"] = average_file_depth(rs_paths)
                results[name] = metrics

            if delete_after:
                subprocess.run(["rm", "-rf", local_path])

        if not os.path.exists(local_path):
            print(f"[!] Repo path does not exist after clone: {local_path}")
        
        count += 1

    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(results, out, indent=2)

    print(f"✅ Done analyzing {count} repositories.")
    print(f"wrote to {os.getcwd()},{output_file}")

main()