import io
import re
from os import listdir
from os.path import isdir, isfile, join

import requests
from tempfile import TemporaryDirectory

import pytesseract
from pdf2image import convert_from_path
from PIL import Image

from bs4 import BeautifulSoup
import docx2txt

PDF_URL = "https://aclanthology.org/2020.bea-1.1.pdf"
IMAGES_URL1 = "https://medlineplus.gov/bonesjointsandmuscles.html"
IMAGES_URL2 = "https://blog.hubspot.com/sales/famous-quotes"
DOCX_PATH = "./NKU Facilities and Resources 2020.docx"
OUTPUT_DIR = "./"

def get_text_in_image(input_image):
    image = Image.open(input_image)
    text = str(pytesseract.image_to_string(image))
    return text

def fetch_image_to_text(url, output_path):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    images = soup.find_all('img')

    if len(images) != 0:
        with open(output_path, "w") as f:
            for image in images:
                try:
                    image_link = image["data-srcset"]
                except:
                    try:
                        image_link = image["data-src"]
                    except:
                        try:
                            image_link = image["data-fallback-src"]
                        except:
                            try:
                                image_link = image["src"]
                            except:
                                pass

                try:
                    response = requests.get(image_link)   
                    text = get_text_in_image(io.BytesIO(response.content))
                    f.write(text)
                except:
                    pass


def pdf_to_text(url, output_path):
    image_file_list = []

    with TemporaryDirectory() as tempdir:
        # Converting PDF to images
        pdf_pages = convert_from_path(url, 500)
        for i, page in enumerate(pdf_pages, start=1):
            filename = join(tempdir, f"{OUTPUT_DIR}/page_{i}.jpg")
            page.save(filename, "JPEG")
            image_file_list.append(filename)

        # Recognizing text from the images using OCR
        with open(output_path, "a") as f:
            for image_file in image_file_list:
                text = str(pytesseract.image_to_string(Image.open(image_file)))
                text = text.replace("-\n", "")
                f.write(text)

def docx_to_text(intput_path, output_path):
    with TemporaryDirectory() as tempdir:
        try:
            text = docx2txt.process(intput_path, tempdir)
            re.sub(r'(\r\n)+', r'\r\n', text)
            with open(output_path, "w") as f:
                image_paths = [join(tempdir, f) for f in listdir(tempdir) if isfile(join(tempdir, f))]
                for image_path in image_paths:
                    text += " " + get_text_in_image(image_path)
                f.write(text)
        except:
            return

# Unit test
def main():
    output_path = join(OUTPUT_DIR, "out_docx_text.txt")
    fetch_image_to_text(IMAGES_URL2, output_path)

if __name__ == "__main__":
	main()
