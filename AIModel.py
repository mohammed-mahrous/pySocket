import enum

HOST = 'localhost'

class AiType(enum.Enum):
    RASA = 'rasa'
    CHATGPT = 'chatGPT'

class AiModel:
    def __init__(self, name:str , host:str , port:int, AuthToken:str, type:str) -> None:
        self.name, self.host , self.port , self.auth = name , host , port, AuthToken,
        self.type = AiType.RASA if type == 'rasa' else AiType.CHATGPT
    def getServerAddress(self) -> tuple[str , int]:
       return (HOST,43007) if self.name == 'Rasa model 1' else (HOST,43008) if self.name == 'Rasa model 2' else (HOST,43009) if self.name == 'Rasa model 3' else (HOST,43006)
    
    @staticmethod
    def getAllModels():
        models:list[AiModel] = [
    AiModel(name='Rasa model 1', host='10.105.173.239', port=8080, AuthToken='mysecrettoken'),
    AiModel(name='Rasa model 2', host='10.105.173.239', port=8081, AuthToken='mysecrettoken'),
    AiModel(name='Rasa model 3', host='10.105.173.239', port=8082, AuthToken='mysecrettoken'),
    AiModel(name='chat-gpt model 1', host='10.105.173.239', port=8083, AuthToken='mysecrettoken'),
        ]
        return models