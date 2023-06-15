from slot_translator import ReviewTranslator
from scrape import save_game_review
import json
import os

if __name__ == '__main__':
    task = """
    https://www.slotjava.it/slot/book-of-ra-deluxe/
    https://www.slotjava.it/slot/sphinx/
    https://www.slotjava.it/slot/the-big-easy/
    https://www.slotjava.it/slot/fruit-sensation/
    https://www.slotjava.it/slot/book-of-ra-magic/
    https://www.slotjava.it/slot/ultra-hot-deluxe/
    https://www.slotjava.it/slot/the-wild-life/
    https://www.slotjava.it/slot/dolphins-pearl-deluxe/
    https://www.slotjava.it/slot/sphinx-wild/
    https://www.slotjava.it/slot/book-of-ra-6/
    https://www.slotjava.it/slot/mega-joker/
    https://www.slotjava.it/slot/katana/
    https://www.slotjava.it/slot/fowl-play-gold/
    https://www.slotjava.it/slot/solar-disc/
    https://www.slotjava.it/slot/da-vinci-diamonds-dual-play/
    https://www.slotjava.it/slot/garden-of-riches/
    https://www.slotjava.it/slot/treasures-of-the-pyramids/
    https://www.slotjava.it/slot/cindereela/
    https://www.slotjava.it/slot/book-of-ra-deluxe-10/
    https://www.slotjava.it/slot/dolphins-pearl/
    https://www.slotjava.it/slot/night-vampire-hd/
    https://www.slotjava.it/slot/columbus-deluxe/
    https://www.slotjava.it/slot/just-jewels-deluxe/
    https://www.slotjava.it/slot/lord-of-the-ocean/
    https://www.slotjava.it/slot/lucky-ladys-charm/
    https://www.slotjava.it/slot/buffalo-toro/
    https://www.slotjava.it/slot/big-bamboo/
    https://www.slotjava.it/slot/golden-ark/
    https://www.slotjava.it/slot/river-queen/
    https://www.slotjava.it/slot/illusionist/
    https://www.slotjava.it/slot/ancient-goddess/
    https://www.slotjava.it/slot/pierino-tenta-la-fortuna/
    https://www.slotjava.it/slot/wild-toro/
    https://www.slotjava.it/slot/book-of-toro/
    https://www.slotjava.it/slot/superstars/
    https://www.slotjava.it/slot/4-fowl-play/
    https://www.slotjava.it/slot/pharaohs-ring/
    https://www.slotjava.it/slot/chicago/
    https://www.slotjava.it/slot/blood-suckers/
    https://www.slotjava.it/slot/gorilla/
    https://www.slotjava.it/slot/cleopatra-gold/
    https://www.slotjava.it/slot/wanted-dead-or-a-wild/
    https://www.slotjava.it/slot/gates-of-olympus/
    https://www.slotjava.it/slot/book-of-duat/
    https://www.slotjava.it/slot/platinum-goddess-ways/
    https://www.slotjava.it/slot/king-neptun/
    https://www.slotjava.it/slot/almighty-reels-garden-of-persephone/
    https://www.slotjava.it/slot/captain-venture/
    https://www.slotjava.it/slot/mr-vegas-2-big-money-tower/
    https://www.slotjava.it/slot/wolf-gold/
    https://www.slotjava.it/slot/the-hand-of-midas/
    https://www.slotjava.it/slot/fortune-coin/
    https://www.slotjava.it/slot/esqueleto-explosivo-2/
    https://www.slotjava.it/slot/generous-jack/
    https://www.slotjava.it/slot/raptor-doublemax/
    https://www.slotjava.it/slot/prometheus-titan-of-fire/
    https://www.slotjava.it/slot/haunted-house/
    https://www.slotjava.it/slot/dragons-clusterbuster/
    https://www.slotjava.it/slot/diamond-multiplier-respin/
    https://www.slotjava.it/slot/book-of-ra-twin-spinner/
    https://www.slotjava.it/slot/wolf-fang-snowfall/
    https://www.slotjava.it/slot/times-of-egypt-egyptian-darkness/
    https://www.slotjava.it/slot/sugar-rush/
    https://www.slotjava.it/slot/ritual-respins/
    https://www.slotjava.it/slot/book-of-power/
    https://www.slotjava.it/slot/sahara-octavian-gaming/
    https://www.slotjava.it/slot/lucky-jack-book-of-rebirth-egyptian-darkness/
    https://www.slotjava.it/slot/the-dog-house-megaways/
    https://www.slotjava.it/slot/treasures-of-the-dead/
    https://www.slotjava.it/slot/pharaohs-reign-mini-max/
    https://www.slotjava.it/slot/stunt-stars/
    https://www.slotjava.it/slot/stolen-treasures/
    https://www.slotjava.it/slot/book-of-baba-yaga/
    https://www.slotjava.it/slot/money-train-3/
    https://www.slotjava.it/slot/take-the-bank/
    https://www.slotjava.it/slot/outlaw/
    https://www.slotjava.it/slot/book-of-inferno/
    https://www.slotjava.it/slot/wild-pumpkins/
    https://www.slotjava.it/slot/captain-wild/
    https://www.slotjava.it/slot/william-tell-the-wild-arrows/
    https://www.slotjava.it/slot/gold-gold-gold/
    https://www.slotjava.it/slot/book-of-wealth/
    https://www.slotjava.it/slot/lavish-lifestyles/
    https://www.slotjava.it/slot/book-of-rampage-2/
    https://www.slotjava.it/slot/fire-spell/
    https://www.slotjava.it/slot/book-of-thieves/
    https://www.slotjava.it/slot/fury-of-odin-megaways/
    https://www.slotjava.it/slot/triple-stop-mermaids-find/
    https://www.slotjava.it/slot/yu-tu-jin-cai-cash-collect/
    https://www.slotjava.it/slot/legends-of-the-colosseum-megaways/
    https://www.slotjava.it/slot/canine-carnage/
    https://www.slotjava.it/slot/snakes-ladders-snake-eyes/
    https://www.slotjava.it/slot/phat-cats-megaways/
    https://www.slotjava.it/slot/treasures-of-fire-scatter-pays/
    https://www.slotjava.it/slot/reel-banks/
    https://www.slotjava.it/slot/fish-eye/
    https://www.slotjava.it/slot/riches-of-rumpelstiltskin-megaways/
    https://www.slotjava.it/slot/3-dancing-monkeys/
    https://www.slotjava.it/slot/four-wealth-creatures/
    """

    urls = task.split("\n")
    urls = [u for u in urls if u != ""]

    for url in urls:
        slug = url.split("/")[-2]
        filename = f"game_reviews/it/{slug}.json"
        save_game_review("it", url)
        if not os.path.exists(filename):
            continue
        f = open(filename, encoding="utf8")
        data = json.load(f)
        print(f"\nTranslation {data['name']}\n============================\n")
        text = data["text"][:6000]
        translation = ReviewTranslator(output_directory="game_reviews/translations", thing_name=data["name"], text=text, mode="translate", remove_faq=True)
        try:
            translation.run_all()
        except:
            continue
