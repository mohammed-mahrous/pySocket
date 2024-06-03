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
            # res = self.aiService.getApiResponseFromMessageAsText(str(data))
            res = self._handleAudioBytes(data,address[0])
            # with open(exportedData.name,'rb') as wav_file:
            #     res = requests.post('http://localhost:5000/transcript', files={'wav-file': wav_file.read()})
            
            # exportedData.close()
            # os.remove(exportedData.name)

            if(res.status_code != 200):
                break
            transcript:str = res.json()['transcript']

            if(len(transcript.strip()) != 0):
                ai_response = self.aiService.getApiResponseFromMessageAsText(transcript.strip())
                print("ai response: {}".format(ai_response))
            
            # start = time.time()
            # import whisper
            # model = whisper.load_model('tiny', device='cpu')
            # results = model.transcribe(audio=exportData.name,language='ar')
            # print('results: {}'.format(results['text']))
            # end = time.time()
            # print(f"Time taken to run the code by function was {end-start} seconds")
            


            # p = pyaudio.PyAudio()
            # stream = p.open(format=FORMAT,
            #         channels=CHANNELS,
            #         rate=RATE,
            #         output=True,)
            # stream.write(audio)
            # with tempfile.NamedTemporaryFile(mode='bx',suffix='.wav',delete=False) as f:
            #     f.write(data)
            #     fileName = f.name
            
            #     with open(fileName,'rb') as rf:
            #         # print('file-bytes-read: {}'.format(rf.read()))
            #         res = requests.post('http://localhost:5000/transcript', files={'wav-file': rf.read()});
            
            # res_json = res.json()
            # print('response_json: {}'.format(res_json))
            res_bytes = base64.b64encode(ai_response)
            conn.send(res_bytes)
        conn.close() # close the connection
        # self.sock.close()


if __name__ == "__main__":
    HOST,PORT = 'localhost', 43007
    server = Server(HOST,PORT)
    server.serve()