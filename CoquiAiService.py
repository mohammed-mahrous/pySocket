import requests
HOST = '10.105.173.241'
PORT = 5000


class CoquiApiService:
    def __init__(self, host:str = HOST, port:int = PORT) -> None:
        self.host, self.port = host, port
        self.__baseUrl = 'http://{}:{}'.format(self.host,self.port)


    def getAudioBytes(self,message:str) -> bytes:
        res = requests.post("{}/tts".format(self.__baseUrl),json={'text': message})
        if(res.status_code != 200):
            return;
        return res.content