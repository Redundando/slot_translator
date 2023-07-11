import json
import os
import re
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from internal_links_anchors import internal_links
from upload_manager import UploadManager


def remove_year(text=""):
    result = text
    for year in ["(2020)", "(2021)", "(2022)", "(2023)", "in 2020", "in 2021", "in 2022", "in 2023", "2020", "2021",
                 "2022", "2023"]:
        result = result.replace(year, "")
    return result


def limit_chars(chars=60, text=""):
    result = text
    while len(result) > chars:
        result = result.rsplit(' ', 1)[0]
    result = result.strip()
    if result[-1] in [",", ";", "-", "|"]:
        result = result[:-1]
    result = result.strip()
    return result


def replace_in_soup(soup=BeautifulSoup, search="", replace=""):
    finder = soup.find_all(string=re.compile(rf"\b{search}\b"))
    for element in finder:
        sub = re.sub(rf"\b{search}\b", replace, element)
        element.replace_with(sub)
        print(f"Replacing {search} with {replace}")


def change_currency_to_dollar(soup=BeautifulSoup):
    finder = soup.find_all(string=re.compile("€"))
    for element in finder:
        element.replace_with(element.replace("€", "$"))
        print("Replacing € with $")
    replace_in_soup(soup, "Euros", "Dollars")
    replace_in_soup(soup, "Euro", "Dollar")
    replace_in_soup(soup, "euros", "Dollars")
    replace_in_soup(soup, "euro", "Dollar")


def remove_sentence(soup=BeautifulSoup, sentence_begin=""):
    pattern = rf"{sentence_begin}.*?[\.\?\!]"
    finder = soup.find_all(string=re.compile(pattern))
    for element in finder:
        print(f"Removing '{sentence_begin} ...': '{re.search(pattern, element.text).group()}'")
        sub = re.sub(pattern, "", element)
        element.replace_with(sub)


def has_h2_before_paragraph(soup=BeautifulSoup):
    element = soup.find(["h2", "p"])
    if element:
        return element.name == "h2"
    return False


def remove_lead_in_head_line(soup=BeautifulSoup):
    if not has_h2_before_paragraph(soup):
        return
    soup.find("h2").decompose()


def proper_capitalize_headlines(soup=BeautifulSoup):
    headlines = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
    for headline in headlines:
        if headline.text == headline.text.upper() and len(headline.text) >= 5:
            print(f"Fixing capitalisation in {headline}")
            text = headline.text
            headline.string = text.title()


def is_anchor_in_soup(anchor="", soup=BeautifulSoup):
    pattern = rf"\b{anchor}\b"
    finder = soup.find_all(string=re.compile(pattern))
    for element in finder:
        if element.parent.name in ["p", "li"]:
            return True
    return False


def add_link_to_first_anchor(anchor="", url="", soup=BeautifulSoup):
    pattern = rf"\b{anchor}\b"
    finder = soup.find_all(string=re.compile(pattern))
    for element in finder:
        if element.parent.name in ["p", "li"]:
            element.replace_with(add_link_element(anchor, url, element))
            return


def add_link_element(anchor="", url="", element=BeautifulSoup):
    print(f"Adding link to {url} to {anchor}")
    html = str(element)
    html = html.replace(anchor, f"<a href=\"{url}\">{anchor}</a>", 1)
    return BeautifulSoup(html, "html.parser")


class SlotFixer:

    DIR = "game_reviews/fix_log"

    def __init__(self, url="", uploader=UploadManager):
        self.data = {}
        self.data["url"] = url
        self.data["slug"] = url.split("/")[-2] if url[-1] == "/" else url.split("/")[-1]
        self.data["filename"] = f'{self.DIR}/{self.data["slug"]}.json'
        self.open_file()
        if self.data.get("save_status") and self.data.get("save_status") == "Page Saved":
            return
        self.save_file()
        self.uploader = uploader
        uploader.goto_slot_page_admin(slug=self.data["slug"])
        self.get_html()
        self.soup = BeautifulSoup(self.data["html"], "html.parser")
        self.run_fixes()

    def create_dir(self):
        if not os.path.exists(self.DIR):
            os.makedirs(self.DIR)

    def run_fixes(self):
        self.fix_metas()
        self.fix_currency()
        remove_lead_in_head_line(self.soup)
        proper_capitalize_headlines(self.soup)
        self.remove_AI_sentences()
        self.add_anchors_to_links(links=internal_links)
        self.data["new_html"] = str(self.soup)
        self.save_file()
        self.update_content()

    def update_content(self):
        meta_entry = self.uploader.enter_metas(self.data["meta_title"], self.data["meta_desc"])
        html_entry = self.uploader.insert_html(self.data["new_html"])
        save_status = self.uploader.save_review()
        self.data["meta_entry"] = meta_entry
        self.data["html_entry"] = html_entry
        self.data["save_status"] = save_status
        self.save_file()

    def add_anchors_to_links(self, links=[]):
        if not self.data.get("links_added"):
            self.data["links_added"] = [self.data["url"]]
        for link_data in links:
            if link_data["url"] in self.data["links_added"]:
                continue
            if is_anchor_in_soup(link_data["anchor"], self.soup):
                add_link_to_first_anchor(link_data["anchor"], link_data["url"], self.soup)
                self.data["links_added"].append(link_data["url"])
        self.save_file()

    def get_html(self):
        print(f"Downloading data for game {self.data['slug']}")
        self.data["html"] = self.uploader.get_html()
        self.save_file()

    def open_file(self):
        if not os.path.isfile(self.data["filename"]):
            return
        f = open(self.data["filename"], encoding="utf8")
        self.data = json.load(f)

    def save_file(self):
        with open(self.data["filename"], "w", encoding='utf8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_metas(self):
        self.data["meta_title"] = self.uploader.get_title()
        self.data["meta_desc"] = self.uploader.get_desc()
        self.save_file()

    def fix_metas(self):
        if self.data.get("fix_saved"):
            return
        self.get_metas()
        print("Fixing Metas")
        self.data["meta_title"] = remove_year(self.data["meta_title"])
        self.data["meta_title"] = limit_chars(chars=60, text=self.data["meta_title"])
        self.data["meta_desc"] = remove_year(self.data["meta_desc"])
        self.data["meta_desc"] = limit_chars(chars=155, text=self.data["meta_desc"])
        self.data["metas_fixed"] = True
        self.save_file()

    def fix_currency(self):
        change_currency_to_dollar(self.soup)

    def remove_AI_sentences(self):
        remove_sentence(self.soup, "But wait,")
        remove_sentence(self.soup, "But let's not forget")
        remove_sentence(self.soup, "And let's not forget")


def fix_all(urls=[]):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        uploader = UploadManager(page=page)
        for url in urls:
            fixer = SlotFixer(url=url, uploader=uploader)


def load_all_urls_from_xml(url=""):
    req = Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36')
    data = urlopen(req).read()
    soup = BeautifulSoup(data, "xml")
    locs = soup.find_all("loc")
    result = []
    for loc in locs:
        if "/slot/" in loc.text:
            result.append(loc.text)
    return result


if __name__ == "__main__":
    urls = load_all_urls_from_xml(url="https://www.slotjava.com/affiliate_slot-sitemap.xml")
    f = fix_all(urls)
