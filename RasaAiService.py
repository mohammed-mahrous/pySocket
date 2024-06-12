import requests
from AIModel import AiModel
HOST = 'localhost'
PORT = 5005
TOKEN = None
CON_ID = 7


class RasaAiService:
    def __init__(self, Conversation_Id:int=CON_ID, model:AiModel = AiModel('model 1', host=HOST , port=8080, AuthToken=TOKEN)) -> None:
        self.model = model
        self.authToken = self.model.auth
        self.Conversation_Id =  Conversation_Id
        self.__baseUrl = f'http://{self.model.host}:{self.model.port}'
        self.__currentIntent = {}
        self.__allMessages:list[str] = []
        self.__currentMessage:str = None
        self.__params = {'token': self.authToken} if self.authToken else None
        

    def checkServerStatus(self) -> bool:
        endPoint = '/status'
        try:
            res = requests.get(self.__baseUrl+endPoint,params=self.__params)
            if not res.status_code == 200:
                return False
            return True
        except Exception as ex:
            print('exception occured: {}'.format(ex))
            return False
    
    def sendMessage(self,message:str) -> None: 
        endpoint = f'/conversations/{self.Conversation_Id}/messages'
        body = {
        'text':message,
        'sender': 'user'
        }
        try:
            res = requests.post(self.__baseUrl+endpoint,json=body, params=self.__params)
            resJson = res.json()
            resMessage = resJson['latest_message']
            intent:dict = resMessage['intent']
            self.__currentIntent = intent
        except Exception as ex:
            print(f'exception occured: {ex}')

    def __getIntentName(self):
        return self.__currentIntent['name'] if self.__currentIntent != None else None
    

    def triggerIntent(self) -> None:
        endPoint = f'/conversations/{self.Conversation_Id}/trigger_intent'
        try:
            if(self.__currentIntent == None):
                raise Exception(message='no intent was found')
            body = {
            "name": self.__getIntentName()
            }
            res = requests.post(self.__baseUrl+endPoint,json=body,params=self.__params)
            resjson = res.json()
            self.__currentIntent = None
            if not len(resjson['messages']) > 0 :
                self.__currentMessage = None
                return
            messages:list[dict] = resjson['messages']
            text = ''
            if(not len(messages) > 1):
                text = messages[0]['text']
                self.__currentMessage = text;
                self.__allMessages.append(text)
                return
            for message in messages:
                keys = message.keys()
                for key in keys:
                    if key == 'text':
                        text = text + f'{message[key]} \n'
                    if(key == 'image'):
                        pass
                        # text = text + f'صورة : {message[key]} \n'
            self.__currentMessage = text;
            self.__allMessages.append(text)
            return
        except Exception as ex:
            print(f'exception occured: {ex}')

    
    def getApiResponseFromMessageAsText(self, message:str) -> str:
        self.sendMessage(message)
        self.triggerIntent()
        return self.__currentMessage