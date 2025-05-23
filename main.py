import os
import json
import datetime

import functions as itg


DIRECTORY = input("Enter absolute filepath to target directory: ")
BORDER_THICKNESS = int(input("Enter thickness of borders seperating map regions (in pixels): "))

# floodfill all map regions/nodes with unique color
print(f"[{datetime.datetime.now()}] Coloring map regions...")
colors, colored_image = itg.color_map_image(DIRECTORY)
colored_image.save(f"{DIRECTORY}/TEMP_MAP.png")

# read text from map (assuming text to be a single word in each region/node)
print(f"[{datetime.datetime.now()}] Reading map text...")
text_dict = itg.detect_text(DIRECTORY)

# match text to regions/nodes
print(f"[{datetime.datetime.now()}] Identifying regions...")
unmatched_colors = itg.match_text_to_color(text_dict, colors, colored_image)
with open(f"{DIRECTORY}/TEMP_RESULTS.json", "w") as json_file:
    json.dump(text_dict, json_file, indent=4)
itg.cleanup(text_dict, colors, unmatched_colors)
os.remove(f"{DIRECTORY}/TEMP_MAP.png")
os.remove(f"{DIRECTORY}/TEMP_RESULTS.json")

# construct graph
print(f"[{datetime.datetime.now()}] Constructing graph...")
graph_dict = itg.create_graph(text_dict, colored_image, BORDER_THICKNESS)

# save graph as json
with open(f"{DIRECTORY}/graph.json", "w") as json_file:
    json.dump(graph_dict, json_file, indent=4)
print(f"[{datetime.datetime.now()}] Done!") 