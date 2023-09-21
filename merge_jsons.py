import json
import argparse
import os

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-ja", "--json-a",
        type=str,
        help="First json to be merged with the second"
    )
    parser.add_argument(
        "-jb", "--json-b",
        type=str,
        help="Second json to be merged with the first"
    )
    parser.add_argument(
        "-jo", "--json-output",
        type=str,
        help="Output json file name"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="output/jsons",
        help="Folder where the merged output json will be written to"
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()

    if not os.path.exists(os.path.join(args.output, "jsons_merged")):
        os.makedirs(os.path.join(args.output, "jsons_merged"))

    with open(args.json_a) as json_file:
        json_a = json.load(json_file)
    with open(args.json_b) as json_file:
        json_b = json.load(json_file)

    json_a["corrections"].extend(json_b["corrections"])
    new_path = os.path.join(args.output, args.json_output)
    with open(new_path, "w") as json_file:
        json.dump(json_a, json_file, indent=4)
    os.system(f"gzip < {new_path} > {new_path}.gz")
