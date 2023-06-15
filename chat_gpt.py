import openai
import traceback

class ChatGpt:

    API_KEY = "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"
    MAX_TOKENS = 4097 - 100
    ATTEMPTS = 3

    def __init__(self, prompt="", role="", model="gpt-3.5-turbo", max_tokens=-1):
        openai.api_key = ChatGpt.API_KEY
        self.prompt = prompt
        self.role = role
        self.model = model
        self.max_tokens = max_tokens if max_tokens > 0 else (ChatGpt.MAX_TOKENS - len(self.prompt+role) // 3)
        self.task = None


    def run_task(self):
        for i in range(ChatGpt.ATTEMPTS):
            try:
                self.task = openai.ChatCompletion.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=[
                        {"role": "system", "content": self.role},
                        {"role": "user", "content": self.prompt},
                    ]
                )
                return
            except Exception as e:
                print(str(e))
                traceback.print_exc()

    def get_response(self):
        result = ""
        for choice in self.task.choices:
            result += choice.message.content
        return result

    def create_image(self):
        for i in range(ChatGpt.ATTEMPTS):
            try:
                self.task = openai.Image.create(prompt = self.prompt, n=1,size="1024x1024")
                return self.task["data"][0]["url"]
            except Exception as e:
                print((str(e)))
                traceback.print_exc()

