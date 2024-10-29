import socket, requests, time, threading
from RasaAiService import RasaAiService
from ChatGPTAiService import ChatGPTAiService
from AIModel import AiModel , AiType
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



class Server :
    def __init__(self, host:str, port:int, model:AiModel, useCoqui:bool = False, debug:bool = False) -> None:
        self.isDebug = debug
        self.host = host
        self.port = port
        self.sock = socket.socket()
        self.serving = False
        self.sttService = STTServiceFasterWhisper()
        self.aiService = RasaAiService(model=model) if model.type == AiType.RASA else ChatGPTAiService(model=model)
        self.ttsService = CoquiApiService() if useCoqui else TransformersApiService()

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
        dataLen = len(data)
        sample_width = 2 if dataLen % (CHANNELS * 2) == 0 else 4 if dataLen % (CHANNELS * 4) == 0 else 1
        audio = AudioSegment(data,channels=CHANNELS, frame_rate=RATE,sample_width=sample_width)
        exportData = audio.export(out_f='temp-audio-{}-{}.wav'.format(id.replace('.',''), self.__getDateTimeFormatted()),format='wav')
        res = self.sttService.transcriptFromFile(exportData)
        return res
    

    def __is_socket_closed(self,conn: socket.socket) -> bool:
        try:
            # this will try to read bytes without blocking and also without removing them from buffer (peek only)
            data = conn.recv(16, socket.MSG_DONTWAIT | socket.MSG_PEEK)
            if len(data) == 0:
                return True
        except BlockingIOError:
            return False  # socket is open and reading from it would block
        except ConnectionResetError:
            return True  # socket was closed for some other reason
        except Exception as e:
            return False
        return False

    def _recvData(self, conn:socket.socket,):
        data = None
        try:
            conn.settimeout(5.0)
            data = conn.recv(100000 * 2)
        except socket.timeout as e:
            print(e)
        except Exception as e:
            print(e)
        finally:
            conn.settimeout(None)
            return data;


    def __handleConnection(self):
        conn , address = self.sock.accept()
        print("Connection from: " + str(address))
        thread = threading.Thread(target=self.__handleClient, args=(conn,address))
        thread.start()

    
    def _sendData(self , msg:bytes, conn: socket.socket) -> None:
        if(msg):
            MSGLEN = msg.__len__()
            print(f"msg len -> {MSGLEN}")
            totalsent = 0
            while totalsent < MSGLEN:
                sent = conn.send(msg[totalsent:])
                if sent == 0:
                    raise RuntimeError("socket connection broken")
                totalsent = totalsent + sent


    def _SendMsg(self, conn:socket.socket, ai_msg:str):
        msg = self.ttsService.getAudioBytes(message=ai_msg)
        self._sendData(msg, conn)
        print(f"data send - {msg.__len__()}")
        time.sleep(2)
        conn.sendall(bytes("stopped","utf-8"))



    def __handleClient(self, conn:socket.socket, address):
        try:
            print(f'handeling client {address[0]}')
            while True:
                isClosed: bool = self.__is_socket_closed(conn)
                if(isClosed):
                    break
                print(f'starting data while loop')
                end_time = self._getEndTime()
                data = None
                while time.time() < end_time:
                    if self.__is_socket_closed(conn):
                        break
                    recieved = self._recvData(conn)
                    if(recieved):
                        print(f"recieved {recieved.__len__()}")
                        if(data):
                            data+= recieved
                        else:
                            data = recieved
                    else:
                        print('no data yet')
                        continue
                print("while timeout loop ended")
                if not data:
                    conn.send('no data'.encode())
                    continue
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
                if(transcript != None and len(transcript) != 0 and not empty_script):
                    ai_response = self.aiService.getApiResponseFromMessageAsText(transcript.strip())
                    print('ai model {} response to "{}": {}'.format(self.aiService.model.name,address[0],ai_response))
                    if(ai_response):
                        self._SendMsg(ai_msg=ai_response, conn=conn)
        
        except Exception as e:
            print('err {}'.format(e))
        finally:            
            conn.close() # close the connection