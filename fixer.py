import glob
import json
import os
import re
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from upload_manager import UploadManager

from internal_links_anchors import internal_links
#from scrape import load_all_game_urls

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
        if element.parent.name in ["p", "li"]: return True
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

    def __init__(self, url="", uploader=UploadManager):
        self.data = {}
        self.data["url"] = url
        self.data["slug"] = url.split("/")[-2] if url[-1] == "/" else url.split("/")[-1]
        self.data["filename"] = f'game_reviews/fix_log/{self.data["slug"]}.json'
        self.open_file()
        if self.data.get("save_status") and self.data.get("save_status") == "Page Saved":
            return
        self.save_file()
        self.uploader = uploader
        uploader.goto_slot_page_admin(slug=self.data["slug"])
        self.get_html()
        self.soup = BeautifulSoup(self.data["html"], "html.parser")
        self.run_fixes()

    def run_fixes(self):
        self.fix_metas()
        self.fix_currency()
        remove_sentence(self.soup, sentence_begin="But wait,")
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
        if self.data.get("fix_saved") == True:
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
    soup = BeautifulSoup(data,"xml")
    locs = soup.find_all("loc")
    result = []
    for loc in locs:
        if "/slot/" in loc.text:
            result.append(loc.text)
    return result

if __name__ == "__main__":
    urls = load_all_urls_from_xml(url="https://www.slotjava.com/affiliate_slot-sitemap.xml")
    urls=["https://www.slotjava.com/slot/fowl-play-gold/"]
    f = fix_all(urls)
    # html = "<!-- wp:image {\"align\":\"right\"} -->\n<figure class=\"wp-block-image alignright\"><img src=\"https://www.slotjava.com/wp-content/uploads/2023/06/Cornelius-Version-1-300x300.webp\" alt=\"Cornelius\"/></figure>\n<!-- /wp:image -->\n\n<h2>Gameplay features and mechanics</h2>\n<p>Cornelius by NetEnt is not only a game for cat lovers, but for anyone who wants to try their luck and experience the thrill of a slot game. With a 5x4 grid and 1024 ways to win, you'll be purring with excitement as you help Cornelius catch his treats that will reward you with amazing cash prizes.</p>\n<p>If you're a high roller, you might want to consider betting the maximum of €400 per spin to increase your chances of winning big. But if you're more of a scaredy-cat, you can start with a minimum bet of €0.20 and work your way up - just like Cornelius when he's trying to catch a mouse.</p>\n<p>One great feature of Cornelius is that it has medium volatility, which means you can expect to win frequently without having to bet a small fortune. And with an RTP value of 96.04%, you can trust that this game won't leave you feeling like a sad kitty after you play.</p>\n<p>Don't want to risk any real money yet? No problem, just hop onto Play for Fun mode to get a feel for the game mechanics and enjoy seeing Cornelius in action.</p>\n<p>Cornelius might be a cat, but he knows how to have a good time and win big - and you can too with this fun and rewarding slot game!</p>\n<h2>BET RANGE AND RTP VALUE</h2>\n<p>If you're a cautious bettor, Cornelius Slot Game offers you a starting bet of €0.20. Conversely, if you're feeling like a high-roller, you can spin with up to €400 per round. Just remember not to spend all your money in one spin! After all, you need to keep some coins for late-night snacks and luxury cat food.</p>\n<p>The RTP value for Cornelius is 96.04%, which is about average for a slot game. But don't be fooled, Cornelius might seem pretty average at first glance, but with the perfect combination of luck, strategy, and special features, you can earn a hefty sum of coins in no time. And, if you happen to be unlucky, blame Cornelius' cat - he might have been sitting on the lucky button, so just go ahead and give him a scratch to obtain his good mojo!</p>\n<h2>Symbols and Their Values</h2>\n<p>Cornelius is a slot game that features symbols ranging from playing cards to cookies - all with their respective values!</p>\n<p>The lower value symbols are represented by playing cards from 10 to ace. The higher-paying symbols include a fish-shaped toy, a milk jar, a little box, and Cornelius himself. Cornelius is not only the highest paying symbol, but also the mascot of the game. He's a cute little rodent who's always up to something.</p>\n<p>But wait, there's more! The Scatter symbol is a jar of cookies that can land you free spins. And isn't that what we all want? More cookies, I mean, more wins! Land 3 or more of these Scatters and trigger the Free Spins bonus game!</p>\n<p>As if cookies weren't enough, there's also the Cash Drop symbol, which is represented by a plate full of tempting cookies. These symbols can pay out from 0.25 to 3 times your bet in the base game. When three Cash Drop symbols land on the reels, you're in for a treat - the Cash Drop feature is activated!</p>\n<p>To sweeten the deal and add some excitement to the game, there are other special symbols as well. The Up symbol moves Cash Drop symbols and multipliers up by one row, giving you the chance to win even bigger. The Golden Up symbol moves symbols straight to the top row for free. How cool is that? The Adder symbol increases the value of standard symbols at the end of the bonus game, and the Multiplier symbol multiplies the value of Cash Drop symbols and multipliers.</p>\n<p>In short, Cornelius is a game that celebrates all things sweet, cute and furry. With so many symbols and features, you're bound to find something that suits your taste. And if you don't, well, at least you still have cookies! </p>\n<h2>Special Game Features and Bonuses</h2>\n<p>Are you ready to cash in on some serious winnings? The Cornelius slot game has got you covered with its special game features and bonuses. One such feature is the Cash Drop, which appears when three Cash Drop symbols land on the reels. The symbols then drop down one row on each spin while paying out every time they appear. It's like raining cash with each spin!</p>\n<p>Oh, and don't forget the Counter on the right! Set to three and resetting every time a new Cash Drop symbol appears, it's sure to keep your excitement levels high! You might even forget that you are playing a slot game.</p>\n<p>If you are into freebies, then the Free Spins bonus is something you definitely don't want to miss. Landing three or more Scatter symbols can activate the bonus feature, with a predetermined number of free spins to be won. And as if that wasn't enough, there's also a chance to win extra cash prizes. You can thank us later!</p>\n<p>But wait, there's more! Other special symbols can also appear during the Free Spins bonus game. These symbols can help increase the value of the symbols and multipliers, giving you even more chances to win big! With all these special features, we are sure you will be entertained and thrilled while playing Cornelius. </p>\n<h2>Availability on Different Devices</h2>\n<p>Cornelius by NetEnt is a fantastic online slot game that's available on both desktop and mobile devices. This means that you can easily play this game on-the-go or from the comfort of your home.</p>\n<p>And let's be honest, nothing screams 'cool' more than playing an online slot game on your phone while pretending to work during an online meeting. Plus, if your boss catches you, you can always say that you're just practicing your online gambling skills in case you ever get a job as a slot attendant.</p>\n<p>Cornelius is perfect for those who want to escape reality for a while and dive into the world of online casinos. Whether you're stuck in traffic or waiting in line at the DMV, this game will keep you entertained.</p>\n<p>So, go ahead and try Cornelius out. You won't regret it. And who knows, you might even end up winning big and finally being able to afford that trip to Las Vegas you've been dreaming of.</p>\n<h2>FAQ</h2>\n<h3>What is the minimum and maximum bet for Cornelius?</h3>\n<p>The minimum bet for each spin is €0.20, which can be increased to a maximum of €400.</p>\n<h3>What is the RTP value for Cornelius?</h3>\n<p>The RTP value for Cornelius is 96.04%.</p>\n<h3>What is the volatility of Cornelius?</h3>\n<p>The volatility of Cornelius is medium.</p>\n<h3>Are there any special symbols in Cornelius?</h3>\n<p>Yes, there are special symbols including Cash Drop, Up, Golden Up, Adder, and Multiplier.</p>\n<h3>Can I play Cornelius for free?</h3>\n<p>Yes, you can play Cornelius in Play for Fun mode for free.</p>\n<h3>Is there a Wild symbol in Cornelius?</h3>\n<p>No, there is no Wild symbol in Cornelius.</p>\n<h3>Can I play Cornelius on my mobile device?</h3>\n<p>Yes, Cornelius is available for both tablets and smartphones.</p>\n<h3>How is the Cash Drop feature activated?</h3>\n<p>The Cash Drop feature is activated when 3 Cash Drop symbols land on the reels.</p>\n<h2>What we like</h2>\n<ul>\n<li>Interesting gameplay features and mechanics</li>\n<li>Wide bet range for different types of players</li>\n<li>Special symbols and bonuses enhance the game experience</li>\n<li>Playable on desktop and mobile devices</li>\n</ul>\n<h2>What we don't like</h2>\n<ul>\n<li>Limited number of high-paying symbols</li>\n<li>Limited number of special symbols</li>\n</ul>"
    # soup = BeautifulSoup(html, "html.parser")
    # add_link_to_first_anchor("NetEnt", "#", soup)
    # print(soup)
