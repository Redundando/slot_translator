import json
import os

from docx import Document
from htmldocx import HtmlToDocx

from scrape import slugify
from text_manipulator import TextManipulator
from upload_manager import UploadManager


def open_file(filename):
    if not os.path.isfile(filename):
        return None
    f = open(filename, encoding="utf8")
    data = json.load(f, strict=False)
    return data


class ReviewTranslator:

    def __init__(self, thing_name="", thing="slot", filename=None, output_directory="", text="", mode="translate",
                 remove_faq=True, uploader=UploadManager, slug=""):
        self.filename = filename if filename else (slugify(thing_name) + ".json")
        self.output_directory = output_directory
        self.thing = thing
        self.thing_name = thing_name
        self.original_text = text
        self.text_manipulator = TextManipulator(self.output_directory + "/" + self.filename)
        self.text_manipulator.data["original_text"] = self.original_text
        self.text_manipulator.data["slug"] = slug
        self.mode = mode
        self.do_remove_faq = remove_faq
        self.text_manipulator.data["name"] = self.thing_name
        self.text_manipulator.save_file()
        self.uploader = uploader

    def upload_slot_content(self):
        self.publish()
        self.insert_content()

    def publish(self):
        if self.data.get("assume_published"):
            return
        print(f"Publishing {self.thing_name}")
        self.uploader.publish_slot(name=self.thing_name)
        self.text_manipulator.data["assume_published"] = True
        self.text_manipulator.save_file()

    def insert_content(self):
        has_content = self.uploader.has_content(self.text_manipulator.data["slug"])
        if has_content:
            content_status = "Page already has content"
            self.text_manipulator.data["content_status"] = content_status
            self.text_manipulator.save_file()
            return

        admin_page_found = self.uploader.goto_slot_page_admin(slug=self.text_manipulator.data["slug"])
        self.text_manipulator.data["page_status"] = "Page exists"
        if not admin_page_found:
            self.text_manipulator.data["page_status"] = "Page not found_"
            self.text_manipulator.save_file()
            return

        feature_image_status = self.uploader.update_feature_image(name=self.thing_name)

        self.text_manipulator.data["feature_image_status"] = feature_image_status
        if "/uploads/" in feature_image_status:
            content = f"""<!-- wp:image {{"align":"right"}} --><figure class="wp-block-image alignright"><img src='{feature_image_status}' alt='{self.thing_name}'></figure><!-- /wp:image -->{self.generate_html(include_metas=False)[0]}"""
        else:
            content = self.generate_html(include_metas=False)[0]
        content_status = self.uploader.insert_html(html=content)
        author_status = self.uploader.select_author()
        self.text_manipulator.data["author_status"] = author_status
        meta_status = self.uploader.enter_metas(title=self.meta[0].get("meta_title"), description=self.meta[0].get("meta_description"))
        self.text_manipulator.data["meta_status"] = meta_status
        save_status = self.uploader.save_review()
        self.text_manipulator.data["save_status"] = save_status
        self.text_manipulator.data["content_status"] = content_status
        self.text_manipulator.save_file()

    def open_file(self):
        if not os.path.isfile(self.filename):
            return
        f = open(self.filename, encoding="utf8")
        self.data = json.load(f)
        self.data["filename"] = self.filename

    def save_file(self):
        with open(self.filename, "w", encoding='utf8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    @property
    def data(self):
        return self.text_manipulator.data

    def translate_raw(self, attempts=1, force_new=False):
        role = "You are an experienced translator from any language to English."
        prompt = f"""
Below is a review for the slot game "{self.thing_name}".
Can you please translate it into english?
Use style transfer to make the translated text suitable for experienced gamblers.
        
{self.original_text}
        """
        for i in range(attempts):
            self.text_manipulator.new_task(task_name="raw_translation", version=(i + 1), role=role, prompt=prompt,
                                           force_new=force_new)

    @property
    def raw_translation(self):
        if self.mode == "translate":
            max_translation_length = 0
            longest_translation = ""
            for translation in self.data.get("raw_translation"):
                if len(translation["response"]) > max_translation_length:
                    max_translation_length = len(translation["response"])
                    longest_translation = translation["response"]
            return longest_translation
        return self.original_text

    def remove_faq_from_text(self, force_new=False):
        role = "You are an experienced writer in the field of online slot games."
        prompt = f"""
Below is a text about the slot game "{self.thing_name}".
Please remove any part of the text that is like an FAQ.

{self.raw_translation}
        """
        self.text_manipulator.new_task(task_name="raw_translation_without_faq", role=role, prompt=prompt,
                                       force_new=force_new)

    @property
    def raw_translation_without_faq(self):
        if self.do_remove_faq:
            return self.data.get("raw_translation_without_faq")[0]["response"]
        return self.raw_translation

    def generate_topics(self, attempts=1, force_new=False):
        num_topics = max(5, len(self.raw_translation) // 600)
        role = "You are an experienced writer in the field of online slot games."
        prompt = f"""
Below is a review for the slot game "{self.thing_name}".

- Please list the {num_topics} most important topics covered
- Order topics by importance
- Answer with a JSON with the single key "topics"

{self.raw_translation_without_faq}
        """
        for i in range(attempts):
            self.text_manipulator.new_task(task_name="topics", role=role, prompt=prompt, version=(i + 1),
                                           force_new=force_new, json_response=True)

    @property
    def topics(self):
        topics = self.data.get("topics")
        result = []
        for topic in topics:
            result.append(topic.get("response").get("topics"))
        return result

    def rewrite_with_topics(self, attempts=1, force_new=False):
        role = "You are an experienced writer in the field of online slot games."
        for i in range(min(attempts, len(self.topics))):
            topics = "\n".join(self.topics[i])
            prompt = f"""
Below is a review for the slot game "{self.thing_name}".

Please, rewrite the review in a neutral tone of voice. Write subsections covering only the following topics:

{topics}

- The review must be very detailed
- No FAQ
- No Notes
- Respond with a JSON array, one item per topic (use the keys "headline" and "content")

Review: {self.raw_translation}
            """
            self.text_manipulator.new_task(task_name="review_with_topics", role=role, prompt=prompt, version=(i + 1),
                                           force_new=force_new,
                                           json_response=True)

    @property
    def review_with_topics(self):
        reviews = self.data.get("review_with_topics")
        result = []
        for review in reviews:
            review_data = []
            for review_section in review.get("response"):
                review_data.append(review_section)
            result.append(review_data)
        return result

    @property
    def review_text(self):
        result = []
        for review in self.review_with_topics:
            review_text = ""
            for review_section in review:
                review_text += review_section.get("headline") + "\n\n"
                review_text += review_section.get("content") + "\n\n"
            result.append(review_text)
        return result

    def expand_review_item(self, review_item={}, paragraphs=2, force_new=False, version=1, tone_of_voice="funny"):
        task_name = "expand_" + slugify(review_item.get("headline")) + "_" + str(version)
        role = "You are an experienced writer in the field of online slot games."
        if tone_of_voice == "professional":
            tone = "Use a professional voice and tone. Use industry-specific language and terminology, provide detailed and accurate information, and support your argument with statistics, research, and expert opinions."
        if tone_of_voice == "funny":
            tone = "Make a few jokes and funny remarks."

        prompt = f"""
I'm writing a review for the casino slot game "{self.thing_name}".

Below is a JSON with the text for a sub section of this review.

- Please rephrase the content
- {tone}
- Encompass the headline with <h2> tags (capitalize according to AP style)
- Encompass each paragraph with <p> html tags
- Respond with a JSON with two keys: "headline" and "content"!

{review_item}
         """
        self.text_manipulator.new_task(task_name=task_name, role=role, prompt=prompt, version=1, force_new=force_new,
                                       json_response=True)

    def expand_review(self, attempts=1, force_new=False):
        for i in range(min(attempts, len(self.review_with_topics))):
            tone = "funny"
            if (i == 2):
                tone = "professional"
            for review_item in self.review_with_topics[i]:
                self.expand_review_item(review_item=review_item, force_new=force_new, version=(i + 1),
                                        tone_of_voice=tone)

    @property
    def expanded_review_html(self):
        result = []
        for i in range(len(self.review_with_topics)):
            html = ""
            for topic in self.review_with_topics[i]:
                data = self.data.get("expand_" + slugify(topic.get("headline")) + "_" + str(i + 1))[0]
                try:
                    html += data.get("response").get("headline")
                    html += data.get("response").get("content")
                except Exception as e:
                    print(str(e))
            result.append(html)
        return result

    def generate_metas(self, attempts=1, force_new=False):
        role = "You are an experienced writer in the field of online slot games."
        for i in range(min(attempts, len(self.review_text))):
            prompt = f"""
Below is a review of the game "{self.thing_name}".

Please provide the following:

- Bullet lists briefly covering the topic "What we like". (4 bullet points)
- Bullet lists briefly covering the topic "What we don't like". (2 bullet pints)
- SEO optimized meta title with a maximum length of 45 characters. Include the words "play" and "free". Capitalize according to AP rules.
- SEO optimized, neutral meta description, explaining the review with a length of 15 words. Include the words "play" and "free".

Respond with a JSON using the keys "pros" (simple array), "cons" (simple array), "meta_title" and "meta_description". 

Review:
 
{self.review_text[i]}        
            """
            self.text_manipulator.new_task(task_name="meta", role=role, prompt=prompt, version=(i + 1),
                                           force_new=force_new, json_response=True)

    @property
    def meta(self):
        result = []
        for m in self.data.get("meta"):
            result.append(m.get("response"))
        return result

    def generate_faq(self, attempts=1, force_new=False):
        role = "You are an experienced writer in the field of online slot games."
        for i in range(min(attempts, len(self.review_text))):
            prompt = f"""
Below is a review of the game "{self.thing_name}".

Please provide an FAQ:

- 8 questions
- Use simple language and provide practical takeaways.
- Respond with a JSON!
- Use the key "faq" and an array with the keys "question" and "answer". 

Review: {self.raw_translation}
            """
            self.text_manipulator.new_task(task_name="faq", role=role, prompt=prompt, version=(i + 1),
                                           force_new=force_new, json_response=True)

    @property
    def faq(self):
        faqs = self.data.get("faq")
        result = []
        for f in faqs:
            result.append(f.get("response").get("faq"))
        return result

    def generate_dalle_prompt(self, force_new=False):
        role = "You are an experienced writer in the field of online slot games."
        prompt = f"""
        Below is a review of the game "{self.thing_name}".

        Please provide a detailed prompt for DALLE to create a feature image fitting the game
        
        - The image should be in cartoon style
        - The should feature a happy Maya warrior with glasses

        Review: {self.raw_translation}
        """
        self.text_manipulator.new_task(task_name="dalle-prompt", role=role, prompt=prompt, version=1,
                                       force_new=force_new, json_response=False)

    @property
    def dalle_prompt(self):
        return self.data.get("dalle-prompt")[0].get("response")

    def generate_html(self, attempts=1, include_metas=True):
        result = []
        for i in range(attempts):
            html = ""
            if include_metas:
                html += "<h1>" + self.meta[i].get("meta_title") + "</h1>"
            html += self.expanded_review_html[i]

            html += "<h2>FAQ</h2>"
            for faq_item in self.faq[i]:
                html += f"<h3>{faq_item.get('question')}</h3>"
                html += f"<p>{faq_item.get('answer')}</p>"
            html += "<h2>What we like</h2><ul>"
            for pro in self.meta[i].get("pros"):
                html += f"<li>{pro}</li>"
            html += "</ul><h2>What we don't like</h2><ul>"
            for con in self.meta[i].get("cons"):
                html += f"<li>{con}</li>"
            html += "</ul>"
            if include_metas:
                html += "<p><strong>" + self.meta[i].get("meta_title") + "</strong></p>"
                html += "<p><i>" + self.meta[i].get("meta_description") + "</i></p>"
            result.append(html)
        return result

    def generate_docx(self, attempts=1):
        html = self.generate_html(attempts=attempts)
        for i in range(min(attempts, len(html))):
            parser = HtmlToDocx()
            document = Document()
            parser.add_html_to_document(html[i], document)
            filename = self.output_directory + "/" + slugify(self.thing_name) + f" (Version {i + 1}).docx"
            document.save(filename)

    def run_all(self, force_new=False, force_new_meta=False, attempts=1):
        if self.mode == "translate":
            self.translate_raw(attempts=attempts, force_new=force_new)
        if self.do_remove_faq:
            self.remove_faq_from_text(force_new=force_new)
        self.generate_topics(attempts=attempts, force_new=force_new)
        self.rewrite_with_topics(attempts=attempts, force_new=force_new)
        self.expand_review(attempts=attempts, force_new=force_new)
        self.generate_metas(attempts=attempts, force_new=(force_new or force_new_meta))
        self.generate_faq(attempts=attempts, force_new=force_new)
        self.generate_dalle_prompt()
        self.generate_docx(attempts=attempts)


if __name__ == '__main__':
    slot_name = "Cold Spell"
    text = """
    La slot machine Cold Spell è fredda in più di un modo. Un trio di potenti personaggi fanno sentire la loro presenza su cinque rulli e tre file, creando vittorie fino a 9.000x la tua linea di scommessa. Sarete anche ricompensati per l’abbinamento di carte da gioco, tiare, mappe e scrigni del tesoro attraverso i rulli ricoperti di ghiaccio.
    
    Una percentuale di vincita del 95,05% e un’azione ad alta varianza suggerisce che avrete bisogno di ghiaccio nelle vostre vene per far girare queste bobine. Tuttavia, le scommesse partono da soli 0,10 crediti per rotazione, e Novomatic ha gentilmente incluso un paio di caratteristiche bonus che possono fornire vittorie di proporzioni davvero epiche.
    
    Una grafica fantasy e gelida
    Disponibile per giocare nei casinò online che offrono il software di Novomatic, il gioco di slot machine Cold Spell vi trasporta in un regno medievale. Il nobile re vi ha chiesto di rompere l’incantesimo che un angelo di ghiaccio ha posto sulla terra. Per farlo, dovrete localizzare il Mago del Fuoco e convincerlo a sventolare la sua bacchetta magica. Le montagne innevate sullo sfondo evidenziano il pericoloso viaggio che affrontate.
    
    Un rapido sguardo alla tabella dei pagamenti di questa slot a tema fantasy mostra che i simboli delle carte da gioco da Asso a 9 pagano meno. Questi simboli sono seguiti da una mappa, un diadema e un forziere del tesoro. Tuttavia, sono i personaggi che danno vita alla slot online Cold Spell. Il re e l’angelo di ghiaccio pagano lo stesso, con il Mago del Fuoco che riscalda le cose con vittorie fino a 9.000x la tua scommessa.
    
    La nostra recensione della slot Cold Spell ha rivelato che le vincite sono calcolate su 10 linee di pagamento. Anche se avrai le dita intirizzite dal freddo, non avrai impedimento nel far girare questi rulli ricoperti di ghiaccio. I valori delle monete vanno da 0,01 a 1, con un massimo di 10 monete che possono essere puntate su ogni linea di pagamento. Questo significa che potete sfidare le temperature sotto zero a partire da 0,10 crediti, mentre chi ha le tasche più profonde può scommettere un massimo di 100 crediti per giro.
    
    Avvolgetevi al caldo e preparatevi per una sessione volatile. Novomatic ha confermato che il ritorno al giocatore (RTP) della slot machine Cold Spell è piuttosto basso al 95,05%. Il gigante austriaco del gioco d’azzardo ha anche rivelato che questa è una slot online ad alta volatilità. Tuttavia, con vincite fino a 9.000x la vostra linea di scommesse in offerta, come potreste rifiutare un viaggio in questo regno medievale?
    
    Funzioni e simboli della Slot Machine
    Il Mago del Fuoco è la chiave per sperimentare le migliori caratteristiche delle slot machine quando si gioca alla slot Cold Spell online. Non solo il Mago del Fuoco consegna vittorie fino a 9.000x la vostra scommessa di linea come simbolo del gioco che paga di più, ma rappresenta anche il simbolo Wild. Il Mago del Fuoco audace e bello può sostituire tutti i simboli eccetto gli Scatter. Ancora più importante, raddoppia le vittorie quando sostituisce.
    
    La sua bacchetta magica rappresenta il simbolo Scatter. Riceverai 5x, 20x, o 500x la tua puntata ogni volta che atterrerai tre, quattro, o cinque simboli scatter, rispettivamente. Il Mago del Fuoco assegnerà anche 15 giochi gratuiti con tutte le vittorie moltiplicate per 3x. I Respins sono possibili quando sbloccate i giochi gratuiti nella slot online Cold Spell, quindi tenete le dita di ghiaccio incrociate nella speranza di trovare un sacco di bacchette magiche sui rulli.
    
    Si può dire con certezza che il nostro team di recensori di Cold Spell è stato lasciato spiazzato da questo epico rilascio di Novomatic.
    
    Le immagini mozzafiato danno vita a un trio di personaggi quando si gioca alla slot machine Cold Spell. Spererete che il Mago del Fuoco vi onori con la sua presenza su una base frequente di vittorie fino a 9.000x la vostra linea di scommessa. È fantastica la possibilità di sostituire tutti i simboli con quello Wild, ma è la caratteristica dei giochi gratuiti che alza davvero il tiro. Il fatto che tutte le vincite siano triplicate rende questa caratteristica incredibilmente eccitante.
    
    Altre Slot Machine simili
    Dopo aver giocato a Cold Spell gratuitamente, perché non far girare i rulli di Magic Portal di NetEnt? Streghe, stregoni, stregoni e maghi mostrano il loro potere su cinque rulli e 25 linee di pagamento creando vittorie fino a 64.000 monete. Fidatevi di noi, non vi stancherete mai delle vittorie elettriche rese possibili da rotazioni selvagge e giri gratis.
    
    Per un po’ di divertimento con fate e draghi, date un’occhiata alla Slot Fantasy Realm di Amaya. Questa slot a cinque rulli e 25 linee di pagamento vanta animazioni che sono impressionanti quanto le sue caratteristiche bonus. Una regina degli elfi può sbattere il suo bastone a terra per innescare 25 giri gratis con tutte le vittorie raddoppiate. Si può anche vincere il Movie Mayhem Jackpot.
    
    
    
    
    """

    a = ReviewTranslator(output_directory="game_reviews/translations", thing_name=slot_name, text=text, mode="translate", remove_faq=True)
    a.run_all(force_new=False)
