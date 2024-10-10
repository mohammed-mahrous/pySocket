import socket
from RasaAiService import RasaAiService
from ChatGPTAiService import ChatGPTAiService
from AIModel import AiModel , AiType
import requests
import time,os , threading, tempfile
from datetime import datetime
from pydub import AudioSegment 
from TTSServiceCoqui import CoquiApiService
from TTSServiceTransformers import TransformersApiService
from STTServiceFasterWhisper import STTServiceFasterWhisper

WHISPERAIHOST = '10.105.173.63'
WHISPERAIPORT = 5000
CHANNELS = 1
RATE = 16000
SECONDS_AFTER_LOOP = 4
useCoqui:bool = False



class Server :
    def __init__(self, host:str, port:int, model:AiModel) -> None:
        self.host = host
        self.port = port
        self.sock = socket.socket()
        self.serving = False
        self.sttService = STTServiceFasterWhisper()
        self.aiService = RasaAiService(model=model) if model.type == AiType.RASA else ChatGPTAiService(model=model)
        self.ttsService = TransformersApiService()

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

    def _getEndTime(self) -> float:
        return time.time() + SECONDS_AFTER_LOOP
    
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
        res = self.sttService.transcriptFromFile(exportData)
        return res

    def __handleConnection(self):
        conn , address = self.sock.accept()
        print("Connection from: " + str(address))
        thread = threading.Thread(target=self.__handleClient, args=(conn,address))
        thread.start()
        # self.__handleClient(conn=conn,address=address)
    def _sendData(self , msg:bytes, conn: socket) -> None:
        if(msg):
            MSGLEN = msg.__len__()
            print(f"msg len -> {MSGLEN}")
            totalsent = 0
            while totalsent < MSGLEN:
                sent = conn.send(msg[totalsent:])
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent

    def __handleClient(self, conn:socket.socket, address):
        try:
            while True:
                end_time = self._getEndTime()
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
                else: print(f"data recived {data.__len__()}")

                res = self._handleAudioBytes(data,address[0])

                if(res.status_code != 200):
                    print('error in whisper ai request {}'.format(res.reason))
                    break
                transcript:str = res.json()['transcript']
                print('whisper transcript response to "{}" => {}'.format(address[0],transcript))
                empty_script:bool =  transcript.strip() == "ترجمة نانسي قنقر" or transcript.strip() == "اشتركوا في القناة"
                if(empty_script):
                    print('whisper recived no transcripeable audio')
                    # break

                if(transcript != None and len(transcript) != 0 and not empty_script):
                    # resbytes = transcript.encode()
                    # conn.send(resbytes)
                    # time.sleep(0.5)
                    # aiService1 = RasaAiService(model=AiModel(name='model 1', host=RASAHOST, port=8080,AuthToken=RASAAUTHTOKEN),)
                    # aiService2 = RasaAiService(model=AiModel(name='model 2', host=RASAHOST, port=8081,AuthToken=RASAAUTHTOKEN),)
                    # aiService3 = RasaAiService(model=AiModel(name='model 3', host=RASAHOST, port=8082,AuthToken=RASAAUTHTOKEN),)
                    ai_response = self.aiService.getApiResponseFromMessageAsText(transcript.strip())
                    # if(ai_response):
                    #     print(f"ai res len -> {len(ai_response)}")
                    #     print(f"ai res -> {ai_response}")
                    
                    # ai_response2 = aiService2.getApiResponseFromMessageAsText(transcript.strip())
                    # ai_response3 = aiService3.getApiResponseFromMessageAsText(transcript.strip())
                    # print('ai model {} response to "{}": {}'.format(self.aiService.model.name,address[0],ai_response))
                    # print('ai model 2 response to "{}": {}'.format(address[0],ai_response2))
                    # print('ai model 3 response to "{}": {}'.format(address[0],ai_response3))
                    if(ai_response):
                        msg = self.ttsService.getAudioBytes(message=ai_response)
                        self._sendData(msg, conn)
                        
                        # conn.sendall(res_bytes) if res_bytes else print('no response from coqui')
                        time.sleep(2)
                        conn.sendall(bytes("stopped","utf-8"))
        except Exception as e:
            print('err {}'.format(e))
        finally:            
            conn.close() # close the connection

    



if __name__ == "__main__":
    HOST,PORT = 'localhost', 43007

    for model in AiModel.getAllModels():
        serverHost, ServerPort = model.getServerAddress()
        server = Server(host=serverHost,port=ServerPort,model=model)
        t = threading.Thread(target=server.serve, name='{} socket thread'.format(model.name))
        t.start()
    # server = Server(host=HOST, port= PORT, model= AiModel.getAllModels()[0])
    # server.serve()