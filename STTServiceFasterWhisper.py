import requests
from typing import IO , Any
from os import PathLike, remove

HOST = '10.105.173.63'
PORT = 5000


class STTServiceFasterWhisper:
    def __init__(self) -> None:
        self.host , self.port = HOST,PORT
        self.__baseURL__ = f'http://{self.host}:{self.port}'

    
    def transcriptFromFile(self,file:IO[Any]|Any| PathLike):
        with open(file.name,'rb') as wav_file:
            res = requests.post(f'{self.__baseURL__}/transcript', files={'wav-file': wav_file.read()})
        file.close()
        remove(file.name)
        return res