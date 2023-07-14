# slot_translator

The scripts in this repository translate and optimize the slot reviews on slotjava.it and upload the translations to slotjava.com

- You need a [ChatGPT API key](https://platform.openai.com/account/api-keys) to run the scripts.
- Enter the key in __config.py__ (rename __config.py.example__)
- To upload data to slotjava.com, enter the login credentials in __config.py__

There are several python scripts in this project:

## scrape.py
_can be run__

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

- Loads the text stored in the file __slot_review.txt__
- Translates text
- Runs multiple chatGPT prompts to create a coherent English slot review
- Creates two reviews as `docx`in the directory `game_reviews/translations`

## bulk_translator.py
_can be run_

- Takes a list of URLs of slot games
- Runs the full slot translation script for each game as defined in `slot_translator.py`

### Requirements

The scripts need the following packages to be installed (can be done via PyCharm):

- requests
- beautifulsoup4
- openai
- htmldocx
