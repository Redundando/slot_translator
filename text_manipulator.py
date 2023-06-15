import json
import ast
import os.path
import traceback

from chat_gpt import ChatGpt


class TextManipulator:

    MAX_JSON_CONVERSION_TRIES = 3

    def __init__(self, filename=""):
        self.json_conversion_attempts = None
        self.json_conversion_failed = None
        self.json_response = False
        self.chat_gpt = ChatGpt
        self.force_new = None
        self.version = None
        self.role = None
        self.prompt = None
        self.task_name = None
        self.filename = filename
        self.data = {}
        self.open_file()

    def open_file(self):
        if not os.path.isfile(self.filename):
            return
        f = open(self.filename, encoding="utf8")
        self.data = json.load(f)
        self.data["filename"] = self.filename

    def save_file(self):
        with open(self.filename, "w", encoding='utf8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def new_task(self, task_name="", prompt="", role="", version=1, force_new=False, json_response=False, execute=True):
        print(f"Preparing task \033[1;32;40m{task_name} (Version {version})\033[0m")
        self.task_name = task_name
        self.prompt = prompt
        self.role = role
        self.version = version
        self.force_new = force_new
        self.json_response = json_response
        self.json_conversion_failed = False
        self.json_conversion_attempts = 0
        self.chat_gpt = ChatGpt(prompt=prompt, role=role)
        if execute:
            self.run_task()
            self.save_file()

    def add_data_point(self, data):
        if self.data.get(self.task_name) is None:
            self.data[self.task_name] = [data]
            return
        for index, data_version in enumerate(self.data[self.task_name]):
            if data_version["version"] == data["version"]:
                self.data[self.task_name][index] = data
                return
        self.data[self.task_name].append(data)

    def convert_response_to_json(self, data=""):
        self.json_conversion_attempts+=1
        self.json_conversion_failed = False
        try:
            result = json.loads(data, strict=False)
        except Exception as e:
            try:
                print("JSON.loads failed, trying AST conversion")
                result = ast.literal_eval(data)
            except Exception as e:
                print("AST conversion failed")
                print(str(e))
                traceback.print_exc()
                self.json_conversion_failed = True
                result = data
        return result

    def run_chat_gpt(self):
        print("Running ChatGPT")
        self.chat_gpt.run_task()
        response = self.chat_gpt.get_response()
        if self.json_response:
            response = self.convert_response_to_json(response)
        data = {"version":  self.version,
                "response": response,
                "role":     self.role,
                "prompt":   self.prompt,
                "log":      self.chat_gpt.task}
        self.add_data_point(data)
        if self.json_response and self.json_conversion_failed and self.json_conversion_attempts<TextManipulator.MAX_JSON_CONVERSION_TRIES:
            print(f"Retrying to get data that is JSON convertable - attempt {self.json_conversion_attempts+1} / {TextManipulator.MAX_JSON_CONVERSION_TRIES}")
            self.force_new = True
            return self.run_chat_gpt()
        return data

    def retrieve_task(self):
        if not self.data.get(self.task_name):
            return None
        for data in self.data[self.task_name]:
            if data["version"] == self.version:
                print("Task result already stored")
                return data
        return None

    def run_task(self):
        result = self.retrieve_task()
        if self.force_new or result is None:
            result = self.run_chat_gpt()

        return result


"""
a = TextManipulator(filename="game_reviews/translations/test.json")
for i in range(1, 20):
    a.new_task(task_name="haiku",
               prompt="Provide your answer in JSON form. Reply with only the answer in JSON form and include no other commentary. Respond with a JSON object with two keys: 'tennis' (string, A haiku about tennis), 'football' (string, A haiku about football)",
               version=i, force_new=True, json_response=True)
    a.run_task()
    a.save_file()
"""
