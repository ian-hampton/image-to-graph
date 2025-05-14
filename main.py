import os
import json

import datetime

import functions as itg

DIRECTORY = input("Enter absolute filepath to target directory: ")

print(f"[{datetime.datetime.now()}] Coloring map regions...")
colors, colored_image = itg.color_map_image(DIRECTORY)
colored_image.save(f"{DIRECTORY}/TEMP_MAP.png")

print(f"[{datetime.datetime.now()}] Reading map text...")
text_dict = itg.detect_text(DIRECTORY)

print(f"[{datetime.datetime.now()}] Identifying regions...")
text_dict, unmatched_colors = itg.match_text_to_color(text_dict, colors, colored_image)
with open(f"{DIRECTORY}/TEMP_RESULTS.json", "w") as json_file:
    json.dump(text_dict, json_file, indent=4)
text_dict = itg.cleanup(text_dict, colors, unmatched_colors)

# construct graph
print(f"[{datetime.datetime.now()}] Constructing graph...")
graph_dict = itg.create_graph(text_dict, colored_image)

# save graph
os.remove(f"{DIRECTORY}/TEMP_MAP.png")
os.remove(f"{DIRECTORY}/TEMP_RESULTS.json")
with open(f"{DIRECTORY}/graph.json", "w") as json_file:
    json.dump(graph_dict, json_file, indent=4)
print(f"[{datetime.datetime.now()}] Done!") 