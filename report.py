import json
import sys

def main():

    total_size_key = "total"
    filename =  sys.argv[1]
    # Load the JSON file
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        f.close()

    rs_repos = get_repos(data, ".rs")
    print("number of projects containing .rs files: ", len(rs_repos))
    print("out of ", len(data), "total projects")


    sort_by_count(data, ".rs", rs_repos)
    
    print("the ten biggest are")
    for i in range(1,11):
        name = rs_repos[i-1]
        print(i,". " + name)


# get items with ".rs" > 0
def get_repos(data, extension):
    repo_names = []
    for repo_name, repo_info in data.items():
        if repo_info[extension] > 0:
            repo_names.append(repo_name)
    return repo_names

def sort_by_count(data, extension, repo_names):
    # Sort by the count in descending order
    sorted_data = sorted(repo_names, key=lambda x: data[x][extension], reverse=True)


main()