import requests
import json
import subprocess
import sys
import os
from urllib.parse import urljoin

def main():
    input_file, output_file = in_out_filenames('_output.json')
    rs_path_dir = "rs_paths"
    os.makedirs(rs_path_dir, exist_ok=True)

    with open(input_file, 'r') as f:
        data = json.load(f)

    for repo_name, repo_info in data.items():
        if repo_info.get(".rs", 0) <= 0:
            continue

        rs_paths = collect_rs_file_paths(repo_info["clone_url"])
        repo_id = repo_name.replace("/", "_")
        rs_path_file = os.path.join(rs_path_dir, repo_id + ".txt")

        with open(rs_path_file, "w") as out:
            for path in rs_paths:
                out.write(path + "\n")

        repo_info["rs_path_file"] = rs_path_file

    update_json_file(data, output_file)

def collect_rs_file_paths(repo_url):
    archive_url = repo_url + "/+archive/HEAD.tar.gz"
    cmd = ['curl', '-L', archive_url]
    tar_cmd = ['tar', '-tzf', '-']

    curl = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    tar = subprocess.Popen(tar_cmd, stdin=curl.stdout, stdout=subprocess.PIPE, text=True)
    file_list, _ = tar.communicate()
    return [f for f in file_list.strip().split("\n") if f.endswith(".rs")]

def in_out_filenames(output_ext):
    input_file = sys.argv[1]
    root = os.path.splitext(input_file)[0]
    output_file = root + output_ext
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    return input_file, output_file

def update_json_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

main()
