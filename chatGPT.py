import random
from scrape import slugify
import openai
import json
from htmldocx import HtmlToDocx


openai.api_key = "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"

MAX_TOKENS = 4097


def load_json(filename="game_reviews/it/1-left-alive.json"):
    f = open(filename, encoding="utf8")
    data = json.load(f)
    data["filename"] = filename
    return data


def save_json(game_review):
    with open(game_review["filename"], "w", encoding='utf8') as f:
        print(f"Saving {game_review['filename']}")
        json.dump(game_review, f, indent=4, ensure_ascii=False)


def get_gpt_response(chat):
    result = ""
    for choice in chat.choices:
        result += choice.message.content
    return result


def translate(game_review={}, force_translation=False):
    if game_review.get("raw_translation") is not None and not force_translation:
        print("Translation already saved.")
        return
    print(f"Translating {game_review['name']}")
    prompt = f"Below is a review for the slot game '{game_review['name']}'. Can you please translate it into english? Use style transfer to make the translated text suitable for experienced gamblers.\n\n{game_review['text']}"

    translation = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=MAX_TOKENS - len(prompt) // 3,
        messages=[
            {"role": "system", "content": "You are an experienced translator from any language to English."},
            {"role": "user", "content": prompt},
        ]
    )
    game_review["raw_translation_response"] = translation
    review_en = get_gpt_response(translation)
    game_review["raw_translation"] = review_en
    save_json(game_review)


def remove_faq(game_review={}, force_removal=False):
    if game_review.get("raw_translation_without_faq") is not None and not force_removal:
        print("FAQ already removed")
        return
    print(f"Removing FAQ for {game_review['name']}")
    prompt = f"""
        Below is a text about the slot game {game_review['name']}. Please remove any part of the text that is like an FAQ.

    Review: {game_review['raw_translation']}

        """
    task = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=MAX_TOKENS - len(prompt) // 3,

        messages=[
            {"role": "system", "content": "You are an experienced writer in the field of online slot games."},
            {"role": "user", "content": prompt},
        ]
    )
    game_review["force_faq_response"] = task
    raw_translation_without_faq = get_gpt_response(task)
    game_review["raw_translation_without_faq"] = raw_translation_without_faq
    save_json(game_review)

def get_topics(game_review={}, force_new_topics=False):
    if game_review.get("topics") is not None and not force_new_topics:
        print("Topics already established")
        return
    print(f"Generating topics for {game_review['name']}")
    num_topics = max(5,len(game_review['raw_translation_without_faq']) // 325)
    prompt = f"""
    Below is a review for the slot game "{game_review['name']}".

- Please list the {num_topics} most important topics covered
- Order topics by importance
- Answer with a JSON with the single key "topics"

Review: {game_review['raw_translation_without_faq']}

    """
    task = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=MAX_TOKENS - len(prompt) // 3,

        messages=[
            {"role": "system", "content": "You are an experienced writer in the field of online slot games."},
            {"role": "user", "content": prompt},
        ]
    )
    game_review["topics_response"] = task
    topics_string = get_gpt_response(task)
    topics = json.loads(topics_string, strict=False)["topics"]
    game_review["topics"] = topics
    save_json(game_review)
    print(topics)


def rewrite_review(game_review={}, force_rewrite=False):
    if game_review.get("rewritten_review_json") is not None and not force_rewrite:
        print("Review already rewritten")
        return
    print(f"Rewriting review for {game_review['name']}")
    topics = '\n'.join(game_review['topics'])
    prompt = f"""
Below is a review for the slot game "{game_review['name']}".

Please, rewrite the review in a neutral tone of voice. Write subsections covering only the following topics:

{topics}

- The review must be very detailed
- No FAQ
- No Notes
- Respond with a JSON array, one item per topic (use the keys "headline" and "content")

Review: {game_review['raw_translation']}

        """

    task = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=MAX_TOKENS - len(prompt) // 3,

        messages=[
            {"role": "system", "content": "You are an experienced writer in the field of online slot games."},
            {"role": "user", "content": prompt},
        ]
    )
    game_review["rewrite_response"] = task
    rewritten_review_json = json.loads(get_gpt_response(task), strict=False)
    game_review["rewritten_review_json"] = rewritten_review_json
    game_review["rewritten_review_text"] = ""
    for review_item in rewritten_review_json:
        game_review["rewritten_review_text"]+=review_item["headline"]+"\n\n"
        game_review["rewritten_review_text"] += review_item["content"] + "\n\n"
    save_json(game_review)


def expand_review_item(game_review={},review_item={}, force_expansion = False)->{}:
    if game_review.get("expand_"+ slugify(review_item['headline'])) is not None and not force_expansion:
        print(f"Topic already expanded: {review_item['headline']}")
        return game_review["expand_"+ slugify(review_item['headline'])]
    print(f"Expanding topic: {review_item['headline']}")

    prompt = f"""
    I'm writing a review for the slot game "{game_review["name"]}".

Below is a JSON with the text for a sub section of this review.

- Please expand the content to {('two' if random.randint(0,1)==0 else 'three')} paragraphs
- Use professional voice and tone. Use industry-specific language and terminology, provide detailed and accurate information, and support your argument with statistics, research, and expert opinions.
- Encompass the headline with <h2> tags (capitalize according to AP style)
- Encompass each paragraph with <p> html tags
- Respond with a JSON with two keys: "headline" and "content"!

    {review_item}

    """

    task = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=MAX_TOKENS - len(prompt) // 3,

        messages=[
            {"role": "system", "content": "You are an experienced writer in the field of online casino games."},
            {"role": "user", "content": prompt},
        ]
    )

    expanded_item = get_gpt_response(task)
    game_review["expand_" + slugify(review_item['headline'])+"_response"] = task
    save_json(game_review)
    game_review["expand_" + slugify(review_item['headline'])] = json.loads(expanded_item, strict=False)
    save_json(game_review)
    return json.loads(expanded_item, strict=False)


def expand_all_review_items(game_review, force_expansion=False):
    if game_review.get("expanded_review") is not None and not force_expansion:
        print("Review already expanded")
        return
    print("Expanding Review")
    review_items=game_review["rewritten_review_json"]
    expanded_review=[]
    for review_item in review_items:
        expanded_item = expand_review_item(game_review, review_item, force_expansion)
        expanded_review.append(expanded_item)
    game_review["expanded_review"] = expanded_review
    save_json(game_review)

def generate_metas(game_review={}, force_rewrite=False):
    if game_review.get("meta") is not None and not force_rewrite:
        print("Metas already created")
        return
    print(f"Creating Metas for {game_review['name']}")
    prompt = f"""
Below is a review of the game {game_review['name']}.

Please provide the following:

- Bullet lists briefly covering the topic "What we like". (4 bullet points)
- Bullet lists briefly covering the topic "What we don't like". (2 bullet pints)
- SEO optimized meta title with a maximum length of 45 characters. Include the words "play" and "free". Capitalize according to AP rules.
- SEO optimized, neutral meta description, explaining the review with a maximum length of 20 words. Include the words "play" and "free".

Respond with a JSON using the keys "pros" (simple array), "cons" (simple array), "meta_title" and "meta_description". 

Review: {game_review['rewritten_review_text']}

        """

    task = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=MAX_TOKENS - len(prompt) // 3,

        messages=[
            {"role": "system", "content": "You are an experienced SEO writer in the field of online slot games."},
            {"role": "user", "content": prompt},
        ]
    )

    game_review["meta_response"] = task
    meta = get_gpt_response(task)
    print(meta)
    game_review["meta"] = json.loads(meta, strict=False)
    save_json(game_review)


def generate_faq(game_review={}, force_faq=False):
    if game_review.get("faq") is not None and not force_faq:
        print("FAQ already created")
        return
    print(f"Creating FAQ for {game_review['name']}")
    prompt = f"""
    Below is a review of the game {game_review['name']}.

    Please provide an FAQ:

    - 8 questions
    - Use simple language, break down complex concepts into frameworks or models, and provide practical takeaways.

    Respond with a JSON using the key "faq" and an array with the keys "question" and "answer". 

    Review: {game_review['rewritten_review_text']}

    """

    task = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        max_tokens=MAX_TOKENS - len(prompt) // 3,

        messages=[
            {"role": "system", "content": "You are an experienced SEO writer in the field of online slot games."},
            {"role": "user", "content": prompt},
        ]
    )

    game_review["faq_response"] = task
    faq = get_gpt_response(task)
    game_review["faq"] = json.loads(faq, strict=False)["faq"]
    save_json(game_review)

def generate_html(game_review):
    html=""
    html+="<h1>"+game_review["meta"]["meta_title"]+"</h1>"
    html += "<p><strong>Meta description</strong>: " + game_review["meta"]["meta_description"] + "</p>"
    for review_item in game_review["expanded_review"]:
        html+=review_item["headline"]
        html+=review_item["content"]

    html+="<h2>FAQ</h2>"
    for faq_item in game_review["faq"]:
        html+=f"<h3>{faq_item['question']}</h3>"
        html += f"<p>{faq_item['answer']}</p>"
    html+="<h2>What we like</h2><ul>"
    for pro in game_review["meta"]["pros"]:
        html+=f"<li>{pro}</li>"
    html+="</ul><h2>What we don't like</h2><ul>"
    for con in game_review["meta"]["cons"]:
        html+=f"<li>{con}</li>"
    html+="</ul>"

    game_review["html"] = html
    save_json(game_review)

def save_as_docx(game_review={}):
    parser = HtmlToDocx()
    parser.parse_html_string(game_review["html"])

    #new_parser.parse_html_file("html_filename", "docx_filename")


def generate_all(game_review={}, force_new = False):
    translate(game_review, force_new)
    remove_faq(game_review, force_new)
    get_topics(game_review, force_new)
    rewrite_review(game_review, force_new)
    expand_all_review_items(game_review, force_new)
    generate_metas(game_review, force_new)
    generate_faq(game_review, force_new)
    generate_html(game_review)

if __name__ == '__main__':
    game_review = load_json(filename="game_reviews/it/cleopatra.json")
    generate_all(game_review, False)



