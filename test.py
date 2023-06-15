import json
import ast

data = '{"headline": "Playing for free or with real money on certified online casinos","content": "Players have the option to play Lucky Ladys Charm for free on SlotJava without using real money or registration. Its also possible to play with real money by connecting to an online casino that has certifications released by the Italian government, ensuring safety and fairness. Players can also take advantage of no deposit bonuses and free spins to try the game without investing real money."}'

data_dict = ast.literal_eval(data)

print(data_dict["headline"])