import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys
import os
import subprocess


def main():
    # Path to your JSON file containing repository {names, info{}}
    input_file, output_file = in_out_filenames('_output.json')

    # Load the JSON file
    with open(input_file, 'r') as f:
        data = json.load(f)
        f.close()

    count_files_in_all_repositories_git(data, '.rs')
    
    update_json_file(data, output_file)

# reports the total number of projects with .rs files
# reports total number of projects
# returns collection of names of rust projects
def get_rust_projects(filename, extension):
    rust_projects = []
    with open(filename, 'r') as f:
        data = json.load(f)
        f.close()
    
    for repo_name, repo_info in data.items():
        if repo_info[extension] > 0:
            rust_projects.append(repo_name)
    
    print(len(data))
    print(len(rust_projects))

    return rust_projects




#updates the count attribute for all repositories using git
def count_files_in_all_repositories_git(data, extension):
    for repo_name, repo_info in data.items():
        branches = repo_info.get('branches')
        repo_info[extension] = count_files_git(branches, extension)
        #print(repo_name)
        #print(repo_info[extension])

# uses git api to recursively search for files
# with the given extension in the repo
def count_files_git(repo_url, extension):
    # Construct the archive URL
    archive_url = repo_url + '/+archive/HEAD.tar.gz'
    
    # Use curl to download the file listing without cloning
    cmd = ['curl', '-L', archive_url]
    tar_cmd = ['tar', '-tzf', '-']  # Adding -f - so tar reads from stdin
    grep_cmd = ['grep', f'{extension}$']  # Directly passing the extension
    wc_cmd = ['wc', '-l']
    
    # Pipe the commands together
    curl = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    tar = subprocess.Popen(tar_cmd, stdin=curl.stdout, stdout=subprocess.PIPE)
    grep = subprocess.Popen(grep_cmd, stdin=tar.stdout, stdout=subprocess.PIPE)
    wc = subprocess.Popen(wc_cmd, stdin=grep.stdout, stdout=subprocess.PIPE)
    
    # Get the result
    output, _ = wc.communicate()
    count = int(output.strip())
    
    return count

       
#get filenames from args
def in_out_filenames(output_file_extension):
    input_file = sys.argv[1]
    root_name = os.path.splitext(input_file)[0]
    output_file = root_name + output_file_extension

    return input_file, output_file

#updates the count attribute for all repositories using web scraping
def count_files_in_all_repositories(data, extension):
    collect_main_branches(data)
    for repo_name, repo_info in data.items():
        clone_url = repo_info.get('clone_url')
        repo_info[extension] = count_files(clone_url, extension)
 
# dfs traversal of html for the git tree
# counts .rs files for folders in stack, adds folders to stack
# if option quickcount is true, returns early as soon as a .rs file is found
def count_files(branches, extension, quickCount=False):
    stack = branches
    rs_file_count = 0

    while stack:
        current_url = stack.pop()
        tree = get_tree(current_url)
        if not tree:
            continue

        for item in tree.find_all('li'):
            link = item.find('a')
            if not link:
                continue

            # Check if it's a directory or a file
            if 'FileList-item--gitTree' in item['class']:
                # It's a directory, push URL to stack
                file_url = urljoin(current_url, link['href'])
                stack.append(file_url)

            else:
                # Count rs files, or exit early with flag
                if link.text.endswith(extension):
                    print("found rs")
                    rs_file_count += 1
                    if quickCount:
                        return rs_file_count
                    

    return rs_file_count

# iterates over the git clone pages
# gets links to filesystems named "main"
# can be refactored to get all filesystems
def collect_main_branches(data):
    for repo_name, repo_info in data.items():
        clone_url = repo_info.get('clone_url')
        main_url = get_main_branch_url(clone_url)
        if main_url:
            if 'branches' not in repo_info:
                repo_info['branches'] = []
            repo_info['branches'].append(main_url)
        else:
            print("main not found in " + clone_url)

# assumes data objects have a boolean flag mapped in name:values:extension.
# does not make server requests, just observes collected data
def count_projects(data, extension):
    count = 0
    for repo_name, repo_info in data.items():
        if repo_info['rs']:
            count += 1
    return count



# data: dictionary populated from json and collect_main_branches(data)
# counts number of folder urls scraped from href in the git entry pages
# output should match number of clone urls in json
def count_branches(data):
    key = "branches"
    count = 0
    for repo_name, repo_info in data.items():
        branches = repo_info[key]
        count += len(branches)
    return count

# TODO (possibly) get all branches instead of filtering for main

def get_main_branch_url(repo_url):
    response = requests.get(repo_url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Locate the list item with the link to the main branch
    site_content = soup.find('div', class_='Site-content')
    if not site_content:
        return None

    container = site_content.find('div', class_=lambda c: c and 'Container' in c.strip())
    if not container:
        return None

    repo_shortlog = container.find('div', class_='RepoShortlog')
    if not repo_shortlog:
        return None

    reflist = repo_shortlog.find('div', class_='RefList RefList--responsive')
    if not reflist:
        return None

    reflist_items = reflist.find('ul', class_='RefList-items')
    if not reflist_items:
        return None
    
    # Search inside the 'li' element for an 'a' tag containing 'main'
    for item in reflist_items.find_all('li', class_='RefList-item'):
        link = item.find('a')
        if link and link.text.strip().lower() == 'main':
            # Use urljoin to avoid double paths
            return urljoin(repo_url, link['href'])

    return None


def get_tree(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    #print("valid url")

    # Locate the list item with the link to the main branch
    site_content = soup.find('div', class_='Site-content')
    if not site_content:
        return None

    container = site_content.find('div', class_=lambda c: c and 'Container' in c.strip())
    if not container:
        return None
    
    tree_detail = container.find('div', class_='TreeDetail')
    if not tree_detail:
        return None
    

    file_list = tree_detail.find('ol', class_='FileList')
    if not file_list:
        return None
    
    #print("found filelist")
    return file_list
    


def update_json_file(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

main()