import requests, enum
HOST = 'localhost'
PORT = 5005
TOKEN = None
CON_ID = 7

GPTAPIKEY = 'sk-nilecrm-ai-service-VE6DyKAoVVUfnfFYyWwuT3BlbkFJfngKDGNHbMOJkHkzRnvT'


class AiType(enum.Enum):
    RASA = 'rasa'
    CHATGPT = 'chatGPT'

class AiModel:
    def __init__(self, name:str , host:str , port:int, AuthToken:str, useFB=False) -> None:
        self.name, self.host , self.port , self.auth, self.isFB = name , host , port, AuthToken, useFB
    
    def getServerAddress(self) -> tuple[str , int]:
       return (HOST,43007) if self.name == 'Rasa model 1' else (HOST,43008) if self.name == 'Rasa model 2' else (HOST,43009)

    @staticmethod
    def getAllModels():
        models:list[AiModel] = [
    AiModel(name='Rasa model 1', host='10.105.173.239', port=8080, AuthToken='mysecrettoken'),
    AiModel(name='Rasa model 2', host='10.105.173.239', port=8081, AuthToken='mysecrettoken', useFB=True),
    AiModel(name='Rasa model 3', host='10.105.173.239', port=8082, AuthToken='mysecrettoken'),
        ]
        return models
        


class RasaAiService:
    def __init__(self, Conversation_Id:int=CON_ID, model:AiModel = AiModel('model 1', host=HOST , port=8080, AuthToken=TOKEN)) -> None:
        self.model = model
        self.__type = AiType.RASA if self.model != 'chat-gpt' else AiType.CHATGPT
        self.authToken = self.model.auth
        self.Conversation_Id =  Conversation_Id
        self.__baseUrl = f'http://{self.model.host}:{self.model.port}'
        self.__currentIntent = {}
        self.__allMessages:list[str] = []
        self.__currentMessage:str = None
        self.__params = {'token': self.authToken} if self.authToken else None
        

    def checkServerStatus(self) -> bool:
        if(self.__type == AiType.CHATGPT):
            return False;
        endPoint = '/status'
        try:
            res = requests.get(self.__baseUrl+endPoint,params=self.__params)
            if not res.status_code == 200:
                return False
            return True
        except Exception as ex:
            print('exception occured: {ex}'.format(ex))
            return False
    
    def sendMessage(self,message:str) -> None:
        if(self.__type == AiType.CHATGPT):
            return;  
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
        if(self.__type == AiType.CHATGPT):
            return;
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
        if(self.__type == AiType.CHATGPT):
            raise Exception('{} service is not emplimented yet'.format(self.__type));
        self.sendMessage(message)
        self.triggerIntent()
        return self.__currentMessage
    

    # def __getAudioBytesFromMessage(self):
    #     try:
    #         data = self.ttsService.text_to_speech(self.__currentMessage)
    #         return data
    #     except Exception as ex:
    #         print(f'exception occured: {ex}')
    
    # def getApiResponseFromMessageAsSound(self, message:str) -> None:
    #     try:    
    #         if(not self.checkServerStatus()):
    #             raise Exception(message='server status is offline')
    #         self.sendMessage(message)
    #         self.triggerIntent()
    #         if(self.__currentMessage == None):
    #             return
    #         if(len(self.__currentMessage) > 0):
    #             self.__getAudioFromMessage()
    #         else: print('no message was found')
    #     except Exception as exp:
    #         print(f'exception occured: {exp}')
    #         print('closing program')
    #         exit()

    # def getApiResponseFromMessageAsbytes(self, message:str) -> bytes:
    #     try:    
    #         if(not self.checkServerStatus()):
    #             raise Exception(message='server status is offline')
    #         self.sendMessage(message)
    #         self.triggerIntent()
    #         if(self.__currentMessage == None):
    #             return
    #         if(len(self.__currentMessage) > 0):
    #            return self.__getAudioBytesFromMessage()
    #         else: print('no message was found')
    #     except Exception as exp:
    #         print(f'exception occured: {exp}')