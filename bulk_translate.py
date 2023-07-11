import traceback
from playwright.sync_api import sync_playwright
from scrape import get_game_review, load_all_game_urls
from slot_translator import ReviewTranslator
from upload_manager import UploadManager

MIN_REVIEW_CHARS_TO_TRANSLATE = 500
MAX_REVIEW_CHARS = 6000


def bulk_translate_and_upload(playwright, urls=[]):

    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()
    uploader = UploadManager(page=page)

    for url in urls:
        try:
            slug = url.split("/")[-2]
            data = get_game_review(url)
            if len(data["text"]) < MIN_REVIEW_CHARS_TO_TRANSLATE:
                print(f"\n{data['name']} Review text too short\n============================\n")
                continue
            print(f"\nTranslating {data['name']}\n============================\n")
            text = data["text"][:MAX_REVIEW_CHARS]

            translation = ReviewTranslator(output_directory="game_reviews/translations", thing_name=data["name"], text=text, mode="translate",
                                           remove_faq=True, uploader=uploader, slug=slug)
            if translation.data.get("save_status") and translation.data.get("save_status") == "Page Saved":
                print("Page already saved")
                continue
            if translation.data.get("content_status") and translation.data.get("content_status") == "Page already has content":
                print("Page already has content (according to JSON save)")
                continue

            translation.run_all()
            translation.upload_slot_content()

        except Exception as e:
            print(e)
            traceback.print_exc()
            continue


if __name__ == '__main__':
    game_urls = load_all_game_urls("https://www.slotjava.it/sitemap/")
    with sync_playwright() as playwright:
        bulk_translate_and_upload(playwright, urls=game_urls)
