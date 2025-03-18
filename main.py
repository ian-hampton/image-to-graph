import os
import sys
import glob
import random
import json
from typing import Tuple

import datetime

from PIL import Image, ImageDraw
import cv2
import pytesseract

EXTENSIONS = {'.png', '.PNG'}
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
custom_config = r"--psm 8"

def check_pixel(px, mode: str, x: int, y: int) -> bool:
    """
    Checks if a pixel is white.

    Params:
        px: Data from main_image.load().
        mode (str): Image type.
        x (int): x-coordinate of pixel.
        y (int): y-coordinate of pixel.
    """
    
    match mode:
        case 'RGB':
            r, g, b = px[x, y]
            if all(c == 255 for c in (r, g, b)):
                return True
        case 'RGBA':
            r, g, b, a = px[x, y]
            if all(c == 255 for c in (r, g, b)) and a == 255:
                return True
    
    return False

def generate_node_color(colors: set[tuple], mode: str) -> tuple[tuple, tuple]:
    """
    Generates a unique color for a node.

    Params:
        colors (set): Set of RGB/RGBA tuples that have already been chosen.
        mode (str): Image type.

    Returns:
        tuple:
            tuple: RGB/RGBA fill color.
            tuple: RGB/RGBA border color.
    """

    while True:
        
        fill_color = [random.randint(1, 254), random.randint(1, 254), random.randint(1, 254)]
        match mode:
            case 'RGB':
                border_color = (0, 0, 0)
            case 'RGBA':
                fill_color.append(255)
                border_color = (0, 0, 0, 255)
        
        fill_color = tuple(fill_color)
        if fill_color not in colors:
            colors.add(fill_color)
            break

    return fill_color, border_color

def filter_text(text: str) -> str:
    """
    Cleans up text detected by pytesseract.

    Params:
        text (str): Detected text.

    Returns:
        text: Filtered text.
    """

    text = text.strip()
    text = "".join(filter(str.isalnum, text))

    return text

def color_map_image(DIRECTORY: str) -> Tuple[set, Image.Image]:
    """
    Identifies all nodes in an image and colors them a unique color.
    
    Params:
        DIRECTORY (str): Filepath to directory where map images are located.

    Returns:
        tuple:
            set: Set of colors chosen for map regions.
            Image: Colored map image represented a Pillow image data type.
    """
    
    # locate map image
    map_image = None
    files = glob.glob(os.path.join(DIRECTORY, 'map*'))
    for file in files:
        if any(file.endswith(ext) for ext in EXTENSIONS):
            map_image = Image.open(file)
            break
    if map_image is None:
        print("Error: Could not locate map image!")
        sys.exit(1)

    # identify and color nodes
    colors = set()
    width, height = map_image.size
    px = map_image.load()
    for y in range(height):
        for x in range(width):
            if check_pixel(px, map_image.mode, x, y):
                fill_color, border_color = generate_node_color(colors, map_image.mode)
                ImageDraw.floodfill(map_image, (x, y), fill_color, border_color)
                colors.add(fill_color)
                px = map_image.load()

    return colors, map_image

def detect_text(DIRECTORY: str) -> dict:
    """
    Utilizes OpenCV and pytesseract to detect map text.

    Params:
        DIRECTORY (str): Filepath to directory where map images are located.
    
    Returns:
        dict: Dictionary of text keys and their corresponding info.
    """
    
    text_dict = {}

    # locate text image
    text_image = None
    files = glob.glob(os.path.join(DIRECTORY, 'text*'))
    for file in files:
        if any(file.endswith(ext) for ext in EXTENSIONS):
            text_image = cv2.imread(file)
    if text_image is None:
        print("Error: Could not locate map text image!")
        sys.exit(1)

    # image dilation
    gray = cv2.cvtColor(text_image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    rect_kernal = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    dilation = cv2.dilate(thresh, rect_kernal, iterations=5)
    
    # text detection
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(dilation)
    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        cropped = text_image[y:y+h, x:x+w]
        text = pytesseract.image_to_string(cropped, config=custom_config)
        region_id = filter_text(text)
        text_dict[region_id] = {}
        text_dict[region_id]["cords"] = [int(x + 0.5*w), int(y + 0.5*h)]
        text_dict[region_id]["colors"] = []

    return text_dict

def match_text_to_color(text_dict: dict, colors: set, colored_image: Image.Image) ->  Tuple[dict, set]:
    """
    Matches each block of text to a colored region.

    Params:
        text_dict (dict): Dictionary of text keys and their corresponding info.
        colors (set): Set of all colors used in color_map_image().
        colored_image (Image): A copy of the map image with uniquely colored regions.

    Returns:
        tuple:
            dict: Dictionary of text keys and their corresponding info.
            set: All colors that were not matched to a block of text.
    """

    matched_colors = set()
    px = colored_image.load()

    for key, value in text_dict.items():
        x = value["cords"][0]
        y = value["cords"][1]
        if px[x, y] in colors:
            text_dict[key]["colors"].append(list(px[x, y]))
            matched_colors.add(px[x, y])

    unmatched_colors = colors.difference(matched_colors)

    return text_dict, unmatched_colors

def cleanup(text_dict: dict, colors: set, unmatched_colors: set) -> dict:
    """
    Prompts user to handle stray text and colors.

    Params:
        text_dict (dict): Dictionary of text keys and their corresponding info.
        colors (set): Set of all colors used in color_map_image().
        unmatched_colors (set): Set of all colors that have not been matched to a region.

    Returns:
        dict: Dictionary of text keys and their corresponding info.
    """

    # check if cleanup is needed
    unmatched_text = set()
    for key, value in text_dict.items():
        if value["colors"] == []:
            unmatched_text.add(key)
    if len(unmatched_text) == 0 and len(unmatched_colors) == 0:
        return text_dict

    # list all unmatched colors
    if len(unmatched_colors) > 0:
        print("The following colors have not been matched")
        for color in unmatched_colors:
            print(color)
    
    # list all unmatched text
    if len(unmatched_text) > 0:
        print("The following text has not been matched:")
        for string in unmatched_text:
            print(string)
    
    print("Please handle each unmatched value by manually matching it or skipping it.")
    print("Temporary files have been saved to your target directory to help with this.")

    # handle stray text
    for text in unmatched_text:
        user_choice = input(f"{text} (S/m): ")
        if user_choice.lower() not in ["m", "match"]:
            continue
        while True:
            color = input("Enter BGR color as a comma-separated list: ")
            try:
                color = tuple(val.strip() for val in color.split(","))
            except:
                continue
            if color in colors:
                text_dict[region_id]["colors"].append(color)
                break

    # handle stray colors
    for color in unmatched_colors:
        user_choice = input(f"{color} (S/m): ")
        if user_choice.lower() not in ["m", "match"]:
            continue
        while True:
            region_id = input("Enter region text: ")
            if region_id in text_dict:
                text_dict[region_id]["colors"].append(color)
                break
    
    return text_dict

def main():

    DIRECTORY = input("Enter absolute filepath to target directory: ")

    print(f"[{datetime.datetime.now()}] Coloring map regions...")
    colors, colored_image = color_map_image(DIRECTORY)
    colored_image.save(f"{DIRECTORY}/TEMP_MAP.png")

    print(f"[{datetime.datetime.now()}] Reading map text...")
    text_dict = detect_text(DIRECTORY)
    
    print(f"[{datetime.datetime.now()}] Identifying regions...")
    text_dict, unmatched_colors = match_text_to_color(text_dict, colors, colored_image)
    with open(f"{DIRECTORY}/TEMP_RESULTS.json", "w") as json_file:
        json.dump(text_dict, json_file, indent=4)
    text_dict = cleanup(text_dict, colors, unmatched_colors)

    # construct graph
    print(f"[{datetime.datetime.now()}] Constructing graph...")

    # save graph
    os.remove(f"{DIRECTORY}/TEMP_MAP.png")
    os.remove(f"{DIRECTORY}/TEMP_RESULTS.json")
    print(f"[{datetime.datetime.now()}] Done!") 

if __name__ == "__main__":
    main()