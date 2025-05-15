import os
import sys
import glob
import random
from typing import Tuple

from PIL import Image, ImageDraw
import cv2
import pytesseract

EXTENSIONS = {'.png', '.PNG'}
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
custom_config = r"--psm 8"

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

def tup_to_hex(color_tuple: tuple) -> str:
    """
    Converts RBG or RGBA color to a hexadecimal string.
    """

    result = None
    if len(color_tuple) == 3:
        result = f"{color_tuple[0]:02x}{color_tuple[1]:02x}{color_tuple[2]:02x}"
    elif len(color_tuple) == 4:
        result = f"{color_tuple[0]:02x}{color_tuple[1]:02x}{color_tuple[2]:02x}{color_tuple[3]:02x}"

    return result

def is_significant(x: int, y: int, px, border_color: tuple) -> bool:
    """
    Checks if a pixel is on the border of a region/node.
    """

    adjacent_cords = [(x-1, y), (x+1, y), (x, y-1), (x, y+1)]

    for x, y in adjacent_cords:
        if px[x, y] == border_color:
            return True
            
    return False

def bresenham_circle(x0: int, y0: int, r: int) -> list:

    points = []
    x = 0
    y = r
    d = 3 - 2 * r

    def plot_circle_points(xc, yc, x, y):
        points.extend([
            (xc + x, yc + y),
            (xc - x, yc + y),
            (xc + x, yc - y),
            (xc - x, yc - y),
            (xc + y, yc + x),
            (xc - y, yc + x),
            (xc + y, yc - x),
            (xc - y, yc - x)
        ])

    plot_circle_points(x0, y0, x, y)

    while x <= y:
        x += 1
        if d > 0:
            y -= 1
            d += 4 * (x - y) + 10
        else:
            d += 4 * x + 6
        plot_circle_points(x0, y0, x, y)

    return points

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

    # check image mode
    match map_image.mode:
        case 'RGB':
            white = (255, 255, 255)
        case 'RGBA':
            white = (255, 255, 255, 255)

    # identify and color nodes
    colors = set()
    width, height = map_image.size
    px = map_image.load()
    for y in range(height):
        for x in range(width):
            if px[x, y] == white:
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
            color = input("Enter color as a comma-separated list: ")
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

def create_graph(text_dict: dict, colored_image: Image.Image) -> dict:
    """
    Creates the graph ADT.

    Params:
        text_dict (dict): Dictionary of text keys and their corresponding info.
        colored_image (Image): A copy of the map image with uniquely colored regions.

    Returns:
        dict: Final graph represented as a nested dictionary.
    """

    # create color to text dict
    color_to_text_dict = {}
    for key, value in text_dict.items():
        for color in value["colors"]:
            hex_color = tup_to_hex(color)
            if hex_color is not None:
                color_to_text_dict[hex_color] = key
    
    # create graph dict
    graph_dict = {}
    for key, value in text_dict.items():
        graph_dict[key] = {
            "adjacencyMap": {}
        }

    # check image mode
    match colored_image.mode:
        case 'RGB':
            black = (0, 0, 0)
        case 'RGBA':
            black = (0, 0, 0, 255)

    # build adjacency map
    search_radius = 8
    width, height = colored_image.size
    px = colored_image.load()
    for y in range(height):
        for x in range(width):
            
            node_pixel_color = tup_to_hex(px[x,y])
            if node_pixel_color not in color_to_text_dict or not is_significant(x, y, px, black):
                continue
                
            # identify pixels to check
            # tba - narrow search
            points = bresenham_circle(x, y, search_radius)
            
            # check each pixel in points and match the color to adjacent nodes
            node_text = color_to_text_dict[node_pixel_color]
            for x2, y2 in points:
                adjacent_node_color = tup_to_hex(px[x2, y2])
                if adjacent_node_color in color_to_text_dict and adjacent_node_color != node_pixel_color:
                    # update graph_dict
                    adjacent_text = color_to_text_dict[adjacent_node_color]
                    graph_dict[node_text]["adjacencyMap"][adjacent_text] = True
    
    # sort adjacency maps alphabetically
    for key, value in graph_dict.items():
        value["adjacencyMap"] = dict(sorted(value["adjacencyMap"].items()))

    return graph_dict