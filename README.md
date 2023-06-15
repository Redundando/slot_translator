# slot_translator

Best IDE to run the program: [Pycharm](https://www.jetbrains.com/pycharm/download/)

There are several python scripts in this project:

## scrape.py
_can be run__

- Downloads all slot reviews from slotjava.it
- Stores data as json in directory `game_reviews/it`
- Downloads all images associated with the game and stores them in `images`

This little script is just used to get all the texts from slotjava.it

## chat_gpt.py
_can't be run_

Module containing a class responsible for talking to openAI.

Currently my own API_KEY is stored in here and used.

## text_manipulator.py
_can't be run_

Module containing a class that:
- sends requests to chatGPT
- stores reponses in json file
- re-uses already stored responses when querry is repeated

## slot_translator.py
_can be run_

- Takes a text (defined in the program)
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
