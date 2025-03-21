# About

This script is a work in progress. I wrote it to help me create the graph adts for another project. Currently, it builds the graph adt through image analysis done by OpenCV, Pytesseract, and Pillow. The resulting graph is saved to a JSON file.

## Getting Started

### Prerequisites

Since this script utilizes Pytesseract, you need to have [Google Tesseract OCR](https://github.com/tesseract-ocr/tesseract) installed.
* The script is expecting you to have tesseract installed in C:\Program Files\ but you can change this in main.py if needed.

### Installation

1. Clone the repo.
    ```sh
   git clone https://github.com/ian-hampton/image-to-graph.git
   ```
2. Create a python virtual enviroment for this project using the provided requirements.txt file.

    1. Create the virtual enviroment.
        ```sh
        python -m venv .venv
        ```
    2. Activate the virtual enviroment.
        ```sh
        source .venv\Scripts\activate
        ```
    3. Install project requirements.
        ```sh
        pip install -r requirements.txt
        ```

## Roadmap

- [ ] Add option to change bresenham circle radius.
- [ ] Make the adjacency detection more effecient.
- [ ] Add additional save options?

## Contact

Ian Hampton

Project Link: https://github.com/ian-hampton/image-to-graph
