import json
import os
import re

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from upload_manager import UploadManager


def remove_year(text=""):
    result = text
    for year in ["(2020)", "(2021)", "(2022)", "(2023)", "in 2020", "in 2021", "in 2022", "in 2023", "2020", "2021", "2022", "2023"]:
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
        print(f"Removing '{sentence_begin} ...': '{re.search(pattern,element.text).group()}'")
        sub = re.sub(pattern, "", element)
        element.replace_with(sub)


def has_h2_before_paragraph(soup=BeautifulSoup):
    element = soup.find(["h2", "p"])
    return element.name == "h2"


def remove_lead_in_head_line(soup=BeautifulSoup):
    if not has_h2_before_paragraph(soup):
        return
    soup.find("h2").decompose()

def proper_capitalize_headlines(soup=BeautifulSoup):
    headlines = soup.find_all(["h1","h2","h3","h4","h5","h6"])
    for headline in headlines:
        if headline.text == headline.text.upper() and len(headline.text)>=5:
            print(f"Fixing capitalisation in {headline}")
            text = headline.text
            headline.string = text.title()


class SlotFixer:

    def __init__(self, url="", uploader=UploadManager):
        self.data = {}
        self.data["url"] = url
        self.data["slug"] = url.split("/")[-2] if url[-1] == "/" else url.split("/")[-1]
        self.data["filename"] = f'game_reviews/fix_log/{self.data["slug"]}.json'
        self.save_file()
        self.uploader = uploader
        uploader.goto_slot_page_admin(slug=self.data["slug"])
        self.get_html()
        self.soup = BeautifulSoup(self.data["html"], "html.parser")
        self.fix_metas()
        self.fix_currency()
        remove_sentence(self.soup, sentence_begin="But wait,")
        remove_lead_in_head_line(self.soup)
        proper_capitalize_headlines(self.soup)
        self.remove_AI_sentences()

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


if __name__ == "__main__":
    f = fix_all(["https://www.slotjava.com/slot/gonzos-quest/"])
    #html = "<!-- wp:image {\"align\":\"right\"} -->\n<figure class=\"wp-block-image alignright\"><img src=\"https://www.slotjava.com/wp-content/uploads/2023/06/Gonzos-Quest-Version-1-300x300.webp\" alt=\"Gonzo’s Quest\"/></figure>\n<!-- /wp:image -->\n\n<h2>3D Graphics and Sound Effects</h2>\n<p>Get ready to be blown away by the stunning 3D graphics and sound effects of Gonzo's Quest. This game takes slot graphics to a whole new level, as you witness symbols exploding on the screen as special features are activated!</p>\n<p>I mean, who doesn't want to see some ancient Inca carvings crumble away to make room for even more symbols and potential wins? The graphics create a sense of excitement and awe that really draws you in, and you'll find yourself glued to your screen for hours on end.</p>\n<p>But let's not forget about the sound effects. Gonzo's Quest features realistic sound effects that are often overlooked in other casino slots games. The calls of wild animals can be heard in the background, giving you a sense of being in the jungle. It really is a fully immersive experience that makes you forget about everything else going on around you.</p>\n<p>Overall, the graphics and sound effects of Gonzo's Quest are top-notch and contribute to a one-of-a-kind gaming adventure. With all of the special features and immersive sounds and graphics, it's no wonder that Gonzo's Quest has quickly become a favorite among slot enthusiasts.</p>\n<h2>Get Ready for Some Fun - Special Features - Free Falls and Avalanche</h2>\n<p>Are you ready for an adventure in search of hidden treasures? Gonzo's Quest takes you deep into the jungle to explore the mysteries of the Mayan civilization. And, the fun doesn't stop with just the theme. The game features two exciting special functions – Free Falls and Avalanche, which give players plenty of opportunities to win big.</p>\n<p>In Free Falls mode, which activates when three Gold Mayan symbols line up on the reels, players get a chance to earn free spins. Who doesn't love them? And, upon winning, they automatically proceed to the Avalanche mode. Oh, boy, things get even more exciting here. When you land a winning combination, all symbols that constituted the alignment explode, and new ones fall from above, creating further winning combinations, sort of like a domino effect. The Avalanche mode continues until there are no more winning alignments.</p>\n<p>With these features, you’re not just winning money – you're enjoying an exciting adventure that keeps you hooked for hours.</p>\n<p>This game is perfect for anyone who appreciates a great adventure story with a touch of humor and excitement. Don't take our word for it, give it a spin yourself and see how long you can resist the magnetism of Gonzo's Quest. Just remember to keep your eyes on the screen, or you might miss one of those incredible winning combos!</p>\n<h2>Inspiration from Spanish Conquistadors and Maya Culture</h2>\n<p>Are you ready to embark on a thrilling adventure with Gonzo's Quest? This online slot game takes us back in time to the Spanish conquests of the Americas, where Gonzalo Pizarro (Gonzo) is on a mission to find the fabled city of El Dorado. But instead of pursuing this goal with nobility in mind, Gonzo has chosen to steal the treasure map in order to keep all the riches for himself. Can you blame him?</p>\n<p>The symbols in Gonzo's Quest help to recreate the atmosphere of the legendary city of El Dorado. The various animals and masks sculpted out of stone in the Maya style will transport you back to this mysterious world. But be prepared - Gonzo does not make things easy and you'll need to navigate through various obstacles to claim your prize.</p>\n<p>This slot game features some exciting elements, such as the avalanche mechanic. Instead of traditional spinning reels, the symbols fall into place, often leading to a chain reaction of multiple wins. It's not every day you can cause an avalanche and come out richer for it!</p>\n<p>All in all, Gonzo's Quest is a fun and engaging slot game that offers something a little bit different. With its historical background and engaging characters, it's the perfect game for movie buffs and history enthusiasts alike. Just watch out for Gonzo, he may swindle you out of your treasure!</p>\n<h2>Symbols and Atmosphere of El Dorado</h2>\n<p>The symbols in Gonzo's Quest bring to life the vibrant and mystical atmosphere of the legendary city of El Dorado. I mean, who wouldn’t want to uncover hidden treasure and gold? The animal and mask symbols were cleverly designed to be sculpted in stone in the characteristic Maya style. These symbols include a slithery snake, a soaring bird, a menacing alligator, a slimy fish, as well as depictions of fire, the moon, the Gold Mayan symbol, and even a question mark. </p>\n<p>Forget the usual boring card suits, Gonzo's Quest gives you symbols so beautifully crafted that you’ll want to detach them and put them on your shelving units! The question mark symbol represents the Wild and can replace all other symbols to complete a winning alignment. It’s like having a wild card, but better! </p>\n<p>Just as El Dorado is shrouded in mystery, the overall experience of the game is surrounded by a sense of adventure and excitement as you embark on your quest for riches. It’s like a virtual Indiana Jones treasure hunt, but with less snakes. Plus, the animations and graphics are so polished that you’ll forget that you’re playing a game and not watching a movie.</p>\n<h2>POTENTIAL TO WIN A GENEROUS JACKPOT!</h2>\n<p>If you're looking for a fun and exciting slot machine game that offers a chance to win big, then Gonzo's Quest is the game for you! Before you start playing, you must select the value of each token you'd like to wager, but don't worry, there's no need to break the bank as the minimum bet is just €0.01. On the other hand, if you're feeling lucky and want to bet big, the maximum bet is €50.</p>\n<p>Now, let's talk about what we're all really here for - winning that jackpot! Gonzo's Quest offers a generous jackpot of €112,500, which is definitely worth spinning those reels for. And with an RTP of 95.9%, you've got a great chance of winning big. But that's not all - there's also a multiplier that applies during regular spins. That's right, you could double your win up to a maximum of five times! </p>\n<p>If you're a bit of a risk-taker and enjoy the thrill of the chase, Gonzo's Quest is a great choice. But if you're on a tight budget and prefer to play it safe, don't worry, there are plenty of chances to win without risking too much.</p>\n<p>So what are you waiting for? Give Gonzo's Quest a spin today and see if you have what it takes to win that jackpot. Who knows, you may even be able to retire early and spend your days lounging on a beach sipping margaritas - hey, a girl can dream, right?</p>\n<h2>FAQ</h2>\n<h3>What is the RTP of Gonzo's Quest?</h3>\n<p>The Return to Player (RTP) of Gonzo's Quest is 95.9%.</p>\n<h3>What is the maximum bet in Gonzo's Quest?</h3>\n<p>The maximum bet in Gonzo's Quest is €50.</p>\n<h3>What is the jackpot in Gonzo's Quest?</h3>\n<p>The jackpot in Gonzo's Quest is €112,500.</p>\n<h3>What are the special features in Gonzo's Quest?</h3>\n<p>Gonzo's Quest features two exciting special functions - Free Falls and Avalanche.</p>\n<h3>What is the Wild symbol in Gonzo's Quest?</h3>\n<p>The Wild symbol in Gonzo's Quest is the question mark symbol.</p>\n<h3>What is the theme of Gonzo's Quest?</h3>\n<p>Gonzo's Quest is inspired by the Spanish conquistadors who searched for El Dorado, and it features the protagonist Gonzo who steals the treasure map.</p>\n<h3>What are the graphics like in Gonzo's Quest?</h3>\n<p>The 3D graphics in Gonzo's Quest are simply amazing, and players can enjoy realistic sound effects too.</p>\n<h3>How do the Free Falls and Avalanche features work?</h3>\n<p>The Free Falls feature activates with three Gold Mayan symbols, giving players free spins. The Avalanche feature replaces winning symbols with new ones, with the multiplier increasing up to 15x.</p>\n<h2>What we like</h2>\n<ul>\n<li>Stunning 3D graphics and immersive sound effects.</li>\n<li>Two exciting special functions – Free Falls and Avalanche.</li>\n<li>Inspirational theme based on Spanish Conquistadors and Maya culture.</li>\n<li>Generous jackpot and a multiplier that can be multiplied up to five times.</li>\n</ul>\n<h2>What we don't like</h2>\n<ul>\n<li>May not offer the widest range of betting options.</li>\n<li>RTP is relatively lower compared to some of the other slots.</li>\n</ul>"
    #soup = BeautifulSoup(html, "html.parser")
    #remove_sentence(soup,"But")
    #proper_capitalize_headlines(soup)
    #print(soup)
