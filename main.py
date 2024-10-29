import threading, argparse
from AIModel import AiModel
from server import Server

HOST,PORT = 'localhost', 43007


parser:argparse.ArgumentParser = argparse.ArgumentParser()
parser.add_argument('--coqui', action=argparse.BooleanOptionalAction)
parser.add_argument('--debug', action=argparse.BooleanOptionalAction)



args = parser.parse_args()
coqui = args.coqui
debug = args.debug

useCoqui:bool = True if coqui else False
isDebug = True if debug else False

if __name__ == "__main__":
    for model in AiModel.getAllModels():
        serverHost, ServerPort = model.getServerAddress()
        server = Server(host=serverHost,port=ServerPort,model=model, useCoqui= coqui,debug=isDebug)
        t = threading.Thread(target=server.serve, name='{} socket thread'.format(model.name))
        t.start()