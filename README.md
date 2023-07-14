# slot_translator

The scripts in this repository translate and optimize the slot reviews on slotjava.it and upload the translations to slotjava.com

- You need a [ChatGPT API key](https://platform.openai.com/account/api-keys) to run the scripts.
- Enter the key in `config.py` (rename `config.py.example`)
- To upload data to slotjava.com, enter the login credentials in `config.py`

There are several python scripts in this project:

## scrape.py
_can be run_

- Downloads all slot reviews from slotjava.it
- Stores data as JSON in the directory `game_reviews/it`
- Downloads all images associated with the game and stores them in `images`

This little script is just used to get all the texts from slotjava.it

## chat_gpt.py
_can't be run_

Module containing a class responsible for talking to openAI.

## text_manipulator.py
_can't be run_

Module containing a class that:
- sends requests to chatGPT
- stores responses in JSON file
- re-uses already stored responses when query is repeated

## slot_translator.py
_can be run_

This is the main ChatGPT text manipulation class.

- Loads the text stored in the file `slot_review.txt`
- Translates text
- Runs multiple chatGPT prompts to create a coherent English slot review
- Creates two reviews as `docx`in the directory `game_reviews/translations`

## upload_manager.py
_cannot be run_

This module takes care of the intricacies of uploading reviews to slotjava.com:

- Publish slot via slot manager
- Navigate to the review
- Enter review text
- Pick a feature image
- Enter meta descriptions

This module needs the library [`playwright`](https://playwright.dev/python/). It simulates a user with a browser doing the tasks listed above.

## bulk_translator.py
_can be run_

- Takes a list of URLs of slot games
- Runs the full slot translation script for each game as defined in `slot_translator.py`
- Uploads the translated review to slotjava.com

## image_prompts.py
_can be run_

This module contains a few functions for image creation:

`list_all_image_prompts()`: List all image generation prompts in separate txt files. Those can be used to AI generate feature images via [Midjourney](https://www.midjourney.com/). To automatically run all those prompts a [Midjourney Automation Bot](https://kingmichael.gumroad.com/l/ewuso) can be used.
`add_all_image_datas()`: Adds the filenames of all generated images to the review JSON file.
`create_all_webp_images()`: Transforms all generated images to properly sized _webp_ images with proper filenames.

## fixer.py
_can be run_

Runs a few fixes for all uploaded reviews:

- Shortens metas if they're too long
- Changes all currencies from Euro to Dollar
- If the review starts with a h2 headline, it removes it
- Properly capitalizes headlines
- Removes some blatant AI sentences (e.g. "But wait, there's more!")
- Inserts internal links as defined in `internal_link_anchors.py`

## internal_link_anchors.py

_can't be run_

Contains a list of internal links and anchor texts to be inserted in the review text bodies.

## Requirements

The scripts need the following packages to be installed.

- requests
- beautifulsoup4
- openai
- htmldocx
- Pillow
- playwright

## Contact

Any questions, please reach out via email: arved.kloehn@gmail.com

