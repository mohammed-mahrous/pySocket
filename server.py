import socket
from RasaAiService import RasaAiService , AiType , AiModel
import requests
import time,os, base64 , threading
from datetime import datetime
from pydub import AudioSegment , playback
import pyaudio
from typing import IO , Any




RASAHOST = '10.105.173.239'
RASAPORT = 8080
RASAAUTHTOKEN = 'mysecrettoken'
WHISPERAIHOST = '10.105.173.63'
WHISPERAIPORT = 5000
CHANNELS = 1
RATE = 16000



class Server :
    def __init__(self, host:str, port:int, model:AiModel) -> None:
        self.host = host
        self.port = port
        self.sock = socket.socket()
        self.serving = False
        self.aiService = RasaAiService(model=model)

    def serve(self):
        try:

            self.sock.bind((self.host,self.port))
            self.sock.listen()
            self.serving = True
            while True:
                self.__handleConnection()
        except KeyboardInterrupt:
            print("KeyboardInterrupt exception")
            self.sock.close()
        except Exception as e:
            print("err {}".format(e))
        finally:
            self.sock.close()    
            self.serving = False


    def __getDateTimeFormatted(self) -> str:
        now = datetime.now()
        formatted = '{}-{}-{}-{}-{}'.format(now.day,now.hour,now.minute,now.second,now.microsecond)
        return formatted

    def _handleAudioBytes(self, data:bytes, id:str) -> requests.Response:
        # pass
        dataLen = len(data)
        sample_width = 2 if dataLen % (CHANNELS * 2) == 0 else 4 if dataLen % (CHANNELS * 4) == 0 else 1
        audio = AudioSegment(data,channels=CHANNELS, frame_rate=RATE,sample_width=sample_width)
        exportData = audio.export(out_f='temp-audio-{}-{}.wav'.format(id.replace('.',''), self.__getDateTimeFormatted()),format='wav')
        with open(exportData.name,'rb') as wav_file:
                res = requests.post(f'http://{WHISPERAIHOST}:{WHISPERAIPORT}/transcript', files={'wav-file': wav_file.read()})
        exportData.close()
        os.remove(exportData.name)
        return res

    def __handleConnection(self):
        conn , address = self.sock.accept()
        print("Connection from: " + str(address))
        thread = threading.Thread(target=self.__handleClient, args=(conn,address))
        thread.start()
        # self.__handleClient(conn=conn,address=address)

    def __handleClient(self, conn:socket.socket, address):
        try:
            while True:
                end_time = time.time() + 5;
                # receive data stream. it won't accept data packet greater than 1024 bytes
                data = None
                while time.time() < end_time:
                    if(data):
                        data+= conn.recv(100000 * 2)
                    else:
                        data = conn.recv(100000 * 2)

                if not data:
                    conn.send('no data'.encode())
                    break
                res = self._handleAudioBytes(data,address[0])

                if(res.status_code != 200):
                    print('error in whisper ai request {}'.format(res.reason))
                    break
                transcript:str = res.json()['transcript']
                print('whisper transcript response to "{}" => {}'.format(address[0],transcript))
            
                if(transcript != None and len(transcript) != 0):
                    resbytes = transcript.encode()
                    conn.send(resbytes)
                    time.sleep(0.5)
                    aiService1 = RasaAiService(model=AiModel(name='model 1', host=RASAHOST, port=8080,AuthToken=RASAAUTHTOKEN),)
                    aiService2 = RasaAiService(model=AiModel(name='model 2', host=RASAHOST, port=8081,AuthToken=RASAAUTHTOKEN),)
                    aiService3 = RasaAiService(model=AiModel(name='model 3', host=RASAHOST, port=8082,AuthToken=RASAAUTHTOKEN),)
                    ai_response = aiService1.getApiResponseFromMessageAsText(transcript.strip())
                    ai_response2 = aiService2.getApiResponseFromMessageAsText(transcript.strip())
                    ai_response3 = aiService3.getApiResponseFromMessageAsText(transcript.strip())
                    print('ai model 1 response to "{}": {}'.format(address[0],ai_response))
                    print('ai model 2 response to "{}": {}'.format(address[0],ai_response2))
                    print('ai model 3 response to "{}": {}'.format(address[0],ai_response3))
                    if(ai_response):
                        res_bytes = ai_response.encode()
                        conn.send(res_bytes)
                    time.sleep(0.5)
        except Exception as e:
            print('err {}'.format(e))
        finally:            
            conn.close() # close the connection





if __name__ == "__main__":
    HOST,PORT = 'localhost', 43007

    models = [
    AiModel(name='model 1', host=RASAHOST, port=8080, AuthToken=RASAAUTHTOKEN),
    AiModel(name='model 2', host=RASAHOST, port=8081, AuthToken=RASAAUTHTOKEN),
    AiModel(name='model 3', host=RASAHOST, port=8082, AuthToken=RASAAUTHTOKEN),
    # AiModel(name='chat-gpt', host=RASAHOST, port=8083,socketPort=43006)
    ]
    server = Server(host=HOST, port= PORT, model= models[0])
    server.serve()