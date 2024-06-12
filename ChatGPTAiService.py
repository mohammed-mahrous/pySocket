from openai import OpenAI
from open_ai_env import APIKEY

client = OpenAI(api_key=APIKEY)

class ChatGPTAiService:
    def __init__(self) -> None:
        pass

    def showModels(self) -> str:
        models = client.models.list()
        for model in models: print('model {}'.format(model))

    def sendMessage(self,message:str) -> str:
        res = client.completions.create(
        model="gpt-3.5-turbo-instruct",
        prompt=message,
        temperature=1,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
        )
        return res.choices[0].text.strip()

    def getApiResponseFromMessageAsText(self,message:str) -> str:
        text = self.sendMessage(message=message)
        return text