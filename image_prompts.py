import csv
import glob
import io
import json
import math
import os
import sys

from PIL import Image


def webp_save_with_targetSize(im, filename, target):
    """Save the image as Webp with the given name at best quality that makes less than "target" bytes"""
    # Min and Max quality
    Qmin, Qmax = 15, 96
    # Highest acceptable quality found
    Qacc = -1
    while Qmin <= Qmax:
        m = math.floor((Qmin + Qmax) / 2)

        # Encode into memory and get size
        buffer = io.BytesIO()
        im.save(buffer, format="webp", quality=m)
        s = buffer.getbuffer().nbytes
        print(f"Adjusting filesize for {filename} - currently: {s} bytes")
        if s <= target:
            Qacc = m
            Qmin = m + 1
        elif s > target:
            Qmax = m - 1

    # Write to disk at the defined quality
    if Qacc > -1:
        im.save(filename, format="webp", quality=Qacc)
    else:
        print("ERROR: No acceptable quality factor found", file=sys.stderr)


def de_sluggify(slug=""):
    return slug.replace("-", " ").title()


def list_all_image_prompts(json_directory="game_reviews/translations"):
    jsons = glob.glob(f"{json_directory}/*.json")
    if not os.path.exists("images/prompts"):
        os.makedirs("images/prompts")
    for file in jsons:
        f = open(file, encoding="utf8")
        data = json.load(f)
        dalle_prompt_response = data.get("dalle-prompt")
        if dalle_prompt_response:
            dalle_prompt = dalle_prompt_response[0].get("response")
            txt_file = file.split("\\")[-1].replace(".json", ".txt")
            with open("images/prompts" + "/" + txt_file, 'w', encoding="utf8") as f:
                print(dalle_prompt.replace("\n", " "), file=f)


def read_image_data_csv(directory="game_reviews/images/"):
    files = glob.glob(directory + "image_data_*.*")
    result = []
    for filename in files:
        with open(filename, encoding="utf8") as f:
            reader = csv.DictReader(f)
            result.extend(list(reader))
    return result


def add_image_data_to_json(filename="", image_data=[]):
    print(f"Looking for image data to {filename}")
    f = open(filename, encoding="utf8")
    data = json.load(f)
    raw_images = data.get("raw_images")
    if raw_images is None:
        raw_images = []
    for image in image_data:
        image_prompt = image.get("prompt").replace(" ", "")
        dalle_prompt = data.get("dalle-prompt")
        if dalle_prompt is None:
            print("No DALLE prompt found")
            return
        json_prompt = dalle_prompt[0].get("response").replace("\n", "").replace(" ", "")
        if image_prompt == json_prompt:
            image_filename = image.get("filename")
            raw_images.append(image_filename)
            print(f"Raw feature image found: {image_filename}")
    raw_images = list(set(raw_images))
    data["raw_feature_images"] = raw_images
    with open(filename, "w", encoding='utf8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def create_webp_feature_image(image_filename="", slug="", version=1):
    processed_filename = f"game_reviews/processed_images/{de_sluggify(slug)} (Version {version}).webp"
    if os.path.isfile(processed_filename):
        return None
    print(f"Saving image {processed_filename}")
    image = Image.open("game_reviews/images/" + image_filename)
    webp_save_with_targetSize(image, processed_filename, 95000)
    return processed_filename


def create_webp_feature_images(filename=""):
    f = open(filename, encoding="utf8")
    data = json.load(f)

    image_filenames = data.get("raw_feature_images")
    slug = filename.replace("\\", "/").split("/")[-1].replace(".json", "")
    processed_filenames = data.get("processed_feature_images")
    if processed_filenames is None:
        processed_filenames = []
    if image_filenames is None:
        return
    for index, image_filename in enumerate(image_filenames):

        processed_filename = create_webp_feature_image(image_filename=image_filename, slug=slug, version=index + 1)
        if processed_filename:
            processed_filenames.append(processed_filename)

    data["processed_feature_images"] = list(set(processed_filenames))
    with open(filename, "w", encoding='utf8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def add_all_image_datas(directory="game_reviews/translations"):
    jsons = glob.glob(f"{directory}/*.json")
    image_data = read_image_data_csv()
    for json_file in jsons:
        add_image_data_to_json(filename=json_file, image_data=image_data)


def create_all_webp_images(directory="game_reviews/translations"):
    jsons = glob.glob(f"{directory}/*.json")
    for json_file in jsons:
        create_webp_feature_images(json_file)


if __name__ == "__main__":
    #list_all_image_prompts(json_directory="game_reviews/translations")
    #add_all_image_datas()
    #create_all_webp_images()
    pass
