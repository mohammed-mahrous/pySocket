import socket
from RasaAiService import RasaAiService
import requests
import time,os, base64
from pydub import AudioSegment , playback
import pyaudio
from typing import IO , Any

RASAHOST = '10.105.173.239'
RASAPORT = 5005
WHISPERAIHOST = '10.105.173.63'
WHISPERAIPORT = 5000
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

class Server :
    def __init__(self, host:str, port:int) -> None:
        self.host = host
        self.port = port
        self.sock = socket.socket()
        self.serving = False
        self.aiService = RasaAiService(host=RASAHOST,port=RASAPORT)

    def serve(self):
        self.sock.bind((self.host,self.port))
        self.serving = True
        self.sock.listen()
        self.__handleConnection()
        self.serving = False


    def _handleAudioBytes(self, data:bytes, id:str) -> requests.Response:
        # pass
        dataLen = len(data)
        sample_width = 2 if dataLen % (CHANNELS * 2) == 0 else 4 if dataLen % (CHANNELS * 4) == 0 else 1
        audio = AudioSegment(data,channels=CHANNELS, frame_rate=RATE,sample_width=sample_width)
        exportData = audio.export(out_f='temp-audio-{}.wav'.format(id.replace('.','')),format='wav')
        with open(exportData.name,'rb') as wav_file:
                res = requests.post(f'http://{WHISPERAIHOST}:{WHISPERAIPORT}/transcript', files={'wav-file': wav_file.read()})
        exportData.close()
        os.remove(exportData.name)
        return res

    def __handleConnection(self):
        conn , address = self.sock.accept()
        print("Connection from: " + str(address))
        while True:
            # receive data stream. it won't accept data packet greater than 1024 bytes
            data = conn.recv(100000 * 2)
            if not data:
                break
            res = self._handleAudioBytes(data,address[0])

            if(res.status_code != 200):
                print('error in whisper ai request {}'.format(res.reason))
                break
            transcript:str = res.json()['transcript']

            try:
                if(len(transcript.strip()) != 0 and transcript != None):
                    ai_response = self.aiService.getApiResponseFromMessageAsText(transcript.strip())
                    print("ai response: {}".format(ai_response))
            
                    res_bytes = base64.b64encode(ai_response)
                    conn.send(res_bytes)
            except:
                pass
            
        conn.close() # close the connection


if __name__ == "__main__":
    HOST,PORT = 'localhost', 43007
    server = Server(HOST,PORT)
    server.serve()