#!/usr/bin/env python3
import json
import os
import argparse

def convert_old_to_new(input_json_path, output_json_path, variation_label):
    with open(input_json_path, "r") as f:
        data = json.load(f)

    def convert_category(cat):
        return {
            "key": cat["key"],
            "value": {
                "nodetype": "category",
                "input": "values",
                "content": [
                    {"key": variation_label, "value": cat["value"]}
                ]
            }
        }

    def convert_content(node):
        if isinstance(node, dict):
            if node.get("nodetype") == "category" and node.get("input") == "type":
                node["content"] = [convert_category(c) for c in node["content"]]
                return node
            elif "content" in node:
                node["content"] = [convert_content(c) for c in node["content"]]
                return node
            else:
                return node
        elif isinstance(node, list):
            return [convert_content(c) for c in node]
        else:
            return node

    for corr in data.get("corrections", []):
        corr["data"] = convert_content(corr["data"])

    # JSON kompakt aber mit Einrückung schreiben
    with open(output_json_path, "w") as f:
        json.dump(data, f, indent=2, separators=(",", ": "))

    print(f"Converted JSON saved to {output_json_path}")

def main():
    parser = argparse.ArgumentParser(description="Convert JSONs and add variation labels.")
    parser.add_argument("--input-folder", required=True, help="Folder containing the JSON files to convert.")
    parser.add_argument("--variation", required=True, help="Variation label (e.g., nominal, modify_binnings_up10)")
    args = parser.parse_args()

    for root, _, files in os.walk(args.input_folder):
        for file in files:
            if file.endswith(".json"):
                input_json = os.path.join(root, file)
                output_json = input_json  # überschreibt direkt
                convert_old_to_new(input_json, output_json, args.variation)

main()
