import json
import sys
import matplotlib.pyplot as plt

def main():

    total_size_key = "total"
    filename =  sys.argv[1]

    #filename = output_filtered_repos(filename)

    # Load the JSON file
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        f.close()
    
    rs_repos = [repo_info['name'] for repo_info in data.values()]

    sort_by_count(data, ".rs", rs_repos)
    print("the ten biggest are")
    for i in range(1, 5):
        name = rs_repos[i-1]
        print(i,". " + name)

    plot_by_significance([data[name] for name in rs_repos])

def output_filtered_repos(filename):
   # Load the JSON file
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        f.close()

        rs_repos = get_repos(data, ".rs")

    print("number of projects containing .rs files: ", len(rs_repos))
    print("out of ", len(data), "total projects")

    with open("filtered_rs_repos.json", "w", encoding="utf-8") as out:
        json.dump({name: data[name] for name in rs_repos}, out, indent=2)

    return "filtered_rs_repos.json"
    

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

def plot_by_significance(data):
    # Assuming the JSON structure is a list of dictionaries like [{'size': 100, 'percentage': 25}, ...]
    sizes = [repo['total'] for repo in data]
    rs_counts = [repo['.rs'] for repo in data]
    percentages = [repo['.rs'] / repo['total'] if repo['total'] > 0 else 0 for repo in data]

    #plot the data
    plt.figure(figsize=(10, 6))
    scatter = plt.scatter(sizes, percentages, c=rs_counts, alpha=0.7, edgecolors='k')

    #graph properties
    plt.xscale('log')
    #plt.colorbar(scatter, label='.rs file count')
    plt.xlabel('Total File Count')
    plt.ylabel('Proportion of .rs Files')
    plt.title('Rust File Significance Across Repos')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

main()