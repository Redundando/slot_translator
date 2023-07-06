from playwright.sync_api import sync_playwright

from scrape import get_game_review, load_all_game_urls
from slot_translator import ReviewTranslator
from upload_manager import UploadManager


def bulk_upload(playwright):
    game_urls = load_all_game_urls()

    urls = [u for u in game_urls]

    browser = playwright.chromium.launch(headless=False)
    page=browser.new_page()
    uploader = UploadManager(page=page)

    for url in urls[150:]:
        try:
            slug = url.split("/")[-2]
            data = get_game_review(url)
            if len(data["text"]) < 500:
                print(f"\nReview too short for {data['name']}\n============================\n")
                continue
            print(f"\nTranslation {data['name']}\n============================\n")
            text = data["text"][:6000]
            translation = ReviewTranslator(output_directory="game_reviews/translations", thing_name=data["name"], text=text, mode="translate",
                                           remove_faq=True, uploader=uploader,slug=slug)
            if translation.data.get("save_status") and translation.data.get("save_status") == "Page Saved":
                print("Page already saved")
                continue
            if translation.data.get("content_status") and translation.data.get("content_status") == "Page already has content":
                print("Page already has content (according to JSON save)")
                continue


            if len(translation.meta[0].get("meta_description")) > 140:
                new_meta = True
            else:
                new_meta = False
            translation.run_all(force_new_meta=new_meta, attempts=1)

            translation.publish()
            translation.insert_content()

        except Exception as e:
            print(e)
            continue


if __name__ == '__main__':
    with sync_playwright() as playwright:
        bulk_upload(playwright)
