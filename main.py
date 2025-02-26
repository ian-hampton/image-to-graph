import os
import sys
import glob
import random
from typing import Tuple

import datetime

from PIL import Image, ImageDraw

EXTENSIONS = {'.png', '.PNG'}

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

def main():

    DIRECTORY = input("Enter absolute filepath to target directory: ")
    export = True

    print(f'[{datetime.datetime.now()}] Running...')

    colors, colored_image = color_map_image(DIRECTORY)
    if export:
        colored_image.save(f"{DIRECTORY}/colored.png")

    print(f'[{datetime.datetime.now()}] Done!')

if __name__ == "__main__":
    main()