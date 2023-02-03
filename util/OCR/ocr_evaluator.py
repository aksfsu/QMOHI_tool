import sys
from os.path import join, dirname
from tempfile import TemporaryDirectory
import pandas as pd
from gensim.parsing.preprocessing import strip_multiple_whitespaces, strip_non_alphanum
import re

# from pdf2image import convert_from_path
import cv2

# from pytesseract import image_to_string
# import keras_ocr
import easyocr

OUTPUT_DIR = "./"
TEST_DATA_DIR = "./test_images"

def get_text_in_image_by_tesseract(image_path):
    img = cv2.imread(image_path)
    '''
    # gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv_img)
    thresh_img = cv2.threshold(v, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # thresh_img = cv2.threshold(gray_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    # edges = cv2.Canny(image=img, threshold1=100, threshold2=200)
    cv2.imwrite(image_path[:-4] + "_out" + image_path[-4:], thresh_img)
    return image_to_string(thresh_img, config="--psm 3")
    '''
    return image_to_string(img)

def get_text_in_image_by_keras_ocr(image_path):
    image = keras_ocr.tools.read(image_path)
    pipeline = keras_ocr.pipeline.Pipeline()
    prediction_groups = pipeline.recognize([image])
    return " ".join([prediction[0] for prediction in prediction_groups[0]])

def get_text_in_image_by_easy_ocr(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path, detail=0)
    return " ".join(result)

def pdf_to_text(url):
    text = ""
    image_file_list = []

    with TemporaryDirectory() as tempdir:
        # Converting PDF to images
        pdf_pages = convert_from_path(url, 500)
        for i, page in enumerate(pdf_pages, start=1):
            filename = join(tempdir, f"page_{i}.jpg")
            page.save(filename, "JPEG")
            image_file_list.append(filename)

        # Recognizing text from the images using OCR
        for image_file in image_file_list:
            text += get_text_in_image_by_easy_ocr(image_file)
        text = text.replace("-\n", "")
    return text

def get_tokens(text):
    # Cleaning text
    text = strip_non_alphanum(text.lower())
    text = re.sub(r"[\",#/@;:<>{}`_+=~|\[\]]", " ", text)
    text = strip_multiple_whitespaces(text)
    # Tokenize
    return text.split()

def calculate_overlap(text1, text2):
    tokens1 = get_tokens(text1)
    tokens2 = get_tokens(text2)
    # print(f'tokens1={tokens1}')
    # print(f'tokens2={tokens2}')
    token_union = tokens1 + [word for word in tokens2 if word not in tokens1]
    return len([word for word in tokens2 if word in tokens1]) / len(token_union)

def calculate_metrics(correct_text, result_text):
    correct_tokens = get_tokens(correct_text)
    result_tokens = get_tokens(result_text, True)
    # print(f'tokens1={correct_tokens}')
    # print(f'tokens2={result_tokens}')
    
    tp = len([result_token for result_token in result_tokens if result_token in correct_tokens])
    fp = len(result_tokens) - tp
    fn = len([correct_token for correct_token in correct_tokens if correct_token not in result_tokens])

    recall = tp / (tp + fn)
    precision = tp / (tp + fp)
    fscore = 2 * precision * recall / (precision + recall)
    return recall, precision, fscore

def main():
    if len(sys.argv) < 2:
        exit()

    experiment_file_path = sys.argv[1]
    experiment_df = pd.read_csv(experiment_file_path)

    for i, row in experiment_df.iterrows():
        filename = row["filename"]
        correct_text = row["correct_text"]
        # Tesseract
        # text = get_text_in_image_by_tesseract(join(dirname(experiment_file_path) + "/test_images", filename))

        # Keras-OCR
        # text = get_text_in_image_by_keras_ocr(join(dirname(experiment_file_path) + "/test_images", filename))

        # EasyOCR
        text = get_text_in_image_by_easy_ocr(join(dirname(experiment_file_path) + "/test_images", filename))

        print(f'{filename}')

        # Calculate metrics
        recall, precision, fscore = calculate_metrics(correct_text, text)

        # Export results
        experiment_df.loc[experiment_df["filename"] == filename, "recall"] = round(recall, 3)
        experiment_df.loc[experiment_df["filename"] == filename, "precision"] = round(precision, 3)
        experiment_df.loc[experiment_df["filename"] == filename, "f-score"] = round(fscore, 3)
    experiment_df.to_csv(experiment_file_path, index=False)

if __name__ == "__main__":
	main()
