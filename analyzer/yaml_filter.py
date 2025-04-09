import json
import yaml
import sys

def main():
    yaml_file = sys.argv[1]
    json_file = sys.argv[2]
    output_file = sys.argv[3]

    with open(yaml_file, "r") as yf:
        yaml_data = yaml.safe_load(yf)
        yaml_names = set(entry["name"] for entry in yaml_data)

    with open(json_file, "r") as jf:
        json_data = json.load(jf)

    filtered = {
        name: info
        for name, info in json_data.items()
        if name in yaml_names
    }

    with open(output_file, "w") as out:
        json.dump(filtered, out, indent=2)

    print(f"✅ Filtered {len(filtered)} entries into {output_file}")
    print(f" out of {len(json_data.items())} rs files in json")
    print(f" and    {len(yaml_names)}        rs files in .yaml")
    
main()
