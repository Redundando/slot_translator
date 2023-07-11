from playwright.sync_api import expect, Page
import config

class UploadManager:

    def __init__(self, page=Page):
        self.page = page
        self.login()

    def login(self):
        print("Logging in")
        self.page.goto("http://www.slotjava.com/jpesjr-login")
        self.page.get_by_label("Username or Email Address").fill(config.LOGIN_USER)
        self.page.locator('//input[@id="user_pass"]').fill(config.LOGIN_PASS)
        self.page.locator('//input[@id="wp-submit"]').click()

    @property
    def logged_in(self):
        return self.page.locator('//div[@id="wpadminbar"]').count() > 0

    def publish_slot(self, name=""):
        self.goto_slot_manager()
        self.find_and_click_publish_in_slot_manager(name=name)

    def goto_slot_manager(self):
        if not self.logged_in:
            self.login()
        self.page.goto("https://www.slotjava.com/wp-admin/edit.php?post_type=affiliate_slot&page=slot_manager")

    def find_and_click_publish_in_slot_manager(self, name=""):
        name_to_search = name.replace("`", "'").replace("´", "'").replace("!", "").replace(",", "").replace("#", "").replace("’", "'")
        print(f"Looking for {name_to_search} in Slot Manager")
        self.page.locator('//input[@aria-controls="newSlots"]').fill(name_to_search)
        try:
            publish_button = self.page.locator(f'(//tr[.//td[text()="{name_to_search}"]])//button[2]')
            expect(publish_button).to_be_visible()
            publish_button.click()
            print("Published")
            self.page.wait_for_timeout(5000)
        except Exception as e:
            print(e)

    def has_content(self, slug=""):
        url = f"https://www.slotjava.com/slot/{slug}/"
        print(f"Going to {url}")
        try:
            self.page.goto(url)
            content_box = self.page.locator("//article[1]")
            expect(content_box).to_be_visible()
            return len(content_box.text_content()) > 500
        except Exception as e:
            print(e)
            return False

    def goto_slot_page_admin(self, slug=""):
        if not self.logged_in:
            self.login()
        url = f"https://www.slotjava.com/slot/{slug}/"
        print(f"Going to {url}")
        try:
            self.page.goto(url)
            edit_button = self.page.locator('//li[@id="wp-admin-bar-edit"]//a')
            expect(edit_button).to_be_visible()
            edit_button.click()
            return True
        except Exception as e:
            print(e)
            return False

    def update_feature_image(self, name=""):
        print(f"Updating Feature Image for {name}")
        image_name = name.replace("'", "").replace("`", "").replace("´", "").replace(":", "").replace("!", "").replace(",", "").replace("’", "").replace("&", "").replace("€", "").replace("$", "")
        self.page.locator('//div[@class="editor-post-featured-image__container"]//button').click()
        search_field = self.page.locator('//input[@id="media-search-input"]')
        result = ""
        try:
            # Picking the image containing "(Version 1)" in the name
            search_field.fill(f"{image_name} (Version 1)")
            image = self.page.locator(f'//li[@aria-label="{image_name} (Version 1)"]')
            expect(image).to_be_visible()
            image_file = self.page.locator(f'//li[@aria-label="{image_name} (Version 1)"]//img')
            src = image_file.get_attribute("src")
            result += src
        except Exception as e:
            try:
                # If none was found, we pick the last image (which is the default one from slot manager)
                search_field.fill(f"{image_name}")
                image = self.page.locator(f'//ul[@class="attachments ui-sortable ui-sortable-disabled"]//li[last()]')
                expect(image).to_be_visible()
                image_file = self.page.locator(f'//ul[@class="attachments ui-sortable ui-sortable-disabled"]//li[last()]//img')
                src = image_file.get_attribute("src")
                result += src
            except Exception as e:
                print(e)
                result += "No feature image found"
                return result
        checked = image.get_attribute("aria-checked") == "true"
        if not checked:
            image.click()
        self.page.locator('//textarea[@id="attachment-details-alt-text"]').fill(name)
        self.page.locator('//div[@class="media-toolbar-primary search-form"]//button[text()="Set featured image"]').click()
        return result

    def get_text_editor_field(self):
        try:
            editor = self.page.locator('//textarea[@class="editor-post-text-editor"]')
            expect(editor).to_be_visible()
            return self.page.locator('//textarea[@class="editor-post-text-editor"]')
        except Exception as e:
            print("Switching to text edit mode")
            editor = self.page.locator('//div[@class="editor-styles-wrapper block-editor-writing-flow"]')
            editor.click()
            self.page.keyboard.press("Shift+Control+Alt+M")
            return self.page.locator('//textarea[@class="editor-post-text-editor"]')

    def get_html(self):
        return self.get_text_editor_field().text_content()

    def insert_html(self, html=""):
        print("Inserting HTML")
        try:
            editor = self.get_text_editor_field()
            editor.click()
            self.page.keyboard.press('Control+A')
            self.page.keyboard.press('Delete')
            editor.fill(html)
            return "HTML inserted"
        except Exception as e:
            print(e)
            return f"HTML ERROR: {e}"

    def select_author(self):
        try:
            select = self.page.locator('//select[@name="sumpan_author"]')
            select.select_option('Slotjava Team')
            checkbox = self.page.locator('//input[@id="sumpan_show_author"]')
            checkbox.click()
            return "Slotjava Team Author selected"
        except Exception as e:
            return f"Select Author error: {e}"

    def enter_metas(self, title="", description=""):
        result = ""
        try:
            title_element = self.page.locator('(//div[@class="DraftEditor-editorContainer"])[1]')
            title_element.click()
            self.page.keyboard.press('Control+A')
            self.page.keyboard.press('Delete')
            self.page.keyboard.type(title)
            result += f"Title set: '{title}' ### "
        except Exception as e:
            print(e)
            result += f"Meta Title Error: {e} ### "
        try:
            desc_element = self.page.locator('(//div[@class="DraftEditor-editorContainer"])[2]')
            desc_element.click()
            self.page.keyboard.press('Control+A')
            self.page.keyboard.press('Delete')
            self.page.keyboard.type(description)
            result += f"Meta set: '{description}'"
        except Exception as e:
            print(e)
            result += f"Meta Description Error: {e}"
        return result

    def get_title(self):
        title_element = self.page.locator('(//div[@class="DraftEditor-editorContainer"])[1]')
        return title_element.text_content()

    def get_desc(self):
        desc_element = self.page.locator('(//div[@class="DraftEditor-editorContainer"])[2]')
        return desc_element.text_content()

    def save_review(self):
        try:
            button = self.page.locator(
                '//button[@class="components-button editor-post-publish-button editor-post-publish-button__button is-primary"]'
            )
            button.click()
            return "Page Saved"
        except Exception as e:
            return f"Error saving the page: {e}"
