import os
import sys
import glob
import random
from typing import Tuple

import datetime

from PIL import Image, ImageDraw
import cv2
import pytesseract

EXTENSIONS = {'.png', '.PNG'}
pytesseract.pytesseract.tesseract_cmd = "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

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
                fill_color.append(random.randint(1, 254))
                border_color = (0, 0, 0, 255)
        
        fill_color = tuple(fill_color)
        if fill_color not in colors:
            colors.add(fill_color)
            break

    return fill_color, border_color


def color_map_image(DIRECTORY: str, export=True) -> Tuple[set, Image.Image]:
    """
    Identifies all nodes in an image and colors them a unique color.
    
    Params:
        DIRECTORY (str): Filepath to directory where map images are located.
        export (bool): Saves colored map image as a new file if set to True.

    Returns:
        tuple:
            set: Set of colors chosen for map regions.
            Image: Map image represented a Pillow image data type.
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
                px = map_image.load()

    return colors, map_image

def detect_text(DIRECTORY: str) -> dict:
    """
    """
    
    text_dict = {}

    # locate map image
    text_image_filepath = None
    files = glob.glob(os.path.join(DIRECTORY, 'text_3*'))
    for file in files:
        if any(file.endswith(ext) for ext in EXTENSIONS):
            text_image_filepath = file
    if text_image_filepath is None:
        print("Error: Could not locate map text image!")
        sys.exit(1)

    # preprocessing
    img = cv2.imread(text_image_filepath)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
    rect_kernal = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 20))
    dilation = cv2.dilate(thresh1, rect_kernal, iterations = 1)
    contours, hierarchy = cv2.findContours(dilation, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    copy = img.copy()

    # text detection
    count = 0
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        rect = cv2.rectangle(copy, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cropped = copy[y:y + h, x:x + w]
        text = pytesseract.image_to_string(cropped)
        print(f"Found {text.strip()} at ({x}, {y})!")
        count += 1

    print(f"Total region_ids found: {count}")
    cv2.imwrite("test/copy.png", copy)

    return text_dict

def main():

    DIRECTORY = input("Enter absolute filepath to target directory: ")
    print(f"[{datetime.datetime.now()}] Running...")

    colors, colored_image = color_map_image(DIRECTORY)
    colored_image.save(f"{DIRECTORY}/colored.png")
    print(f"[{datetime.datetime.now()}] Map coloring completed!")
    user_choice = input(f"Hit enter when ready: ")

    text_dict = detect_text(DIRECTORY)

if __name__ == "__main__":
    main()