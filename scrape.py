import json
import os
import re
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import requests
import unicodedata
from bs4 import BeautifulSoup


def slugify(value, allow_unicode=False):
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def get_filename_from_url(url=None):
    if url is None:
        return None
    urlpath = urlsplit(url).path
    return os.path.basename(urlpath)


def load_url(url="") -> BeautifulSoup:
    request_site = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    webpage = urlopen(request_site).read()
    return BeautifulSoup(webpage, 'html.parser')


def download_images(soup: BeautifulSoup) -> []:
    result = []
    images = soup.find_all("img")
    for image in images:
        image_info = {}
        image_info["alt"] = image.get("alt")
        image_info["src"] = image.get("src")
        if image_info["src"]:
            r = requests.get(image_info["src"])
            filename = get_filename_from_url(image_info["src"])
            if filename:
                with open("images/" + filename, "wb") as f:
                    print(f"Downloading image f{filename}")
                    f.write(r.content)
            image_info["filename"] = filename
        result.append(image_info)
    return result


def get_game_review(url="", download_images=False):
    print(f"Retrieving game review {url}")
    review = {}
    soup = load_url(url)
    article = soup.find("article")
    author_info = article.find(class_="author-footer")
    author_info.decompose()
    studio = soup.find("div", {"id": "softwareTracker"})
    if studio:
        review["studio"] = studio.get("data-software")
    else:
        review["studio"] = None
    review["text"] = article.text
    if download_images:
        review["images"] = download_images(article)
        ft_image = soup.find("img", class_="review__slot-image")
        review["featured_image"] = download_images(ft_image.parent)
    review["name"] = soup.find("h1").text
    return review


def save_game_review(language="it", url=""):
    review = get_game_review(url)
    if not os.path.exists("game_reviews/" + language):
        os.makedirs("game_reviews/" + language)
    filename = "game_reviews/" + language + "/" + slugify(review["name"]) + ".json"
    with open(filename, "w", encoding='utf8') as f:
        print(f"Saving {filename}")
        json.dump(review, f, indent=4, ensure_ascii=False)


def load_all_game_urls(url="https://www.slotjava.it/sitemap/"):
    soup = load_url(url)
    links = soup.find_all("a", class_="sitemap__link")
    game_urls = []
    for link in links:
        href = link.get("href")
        if "/slot/" in href:
            game_urls.append(href)
    return game_urls


def save_all_game_reviews(language="it", sitemap="https://www.slotjava.it/sitemap/"):
    game_urls = load_all_game_urls(sitemap)
    for game_url in game_urls:
        save_game_review(language, game_url)


if __name__ == '__main__':
    pass
