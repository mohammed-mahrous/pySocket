import threading, argparse
from AIModel import AiModel
from server import Server


parser:argparse.ArgumentParser = argparse.ArgumentParser()
parser.add_argument('--coqui', action=argparse.BooleanOptionalAction)

HOST,PORT = 'localhost', 43007

args = parser.parse_args()
coqui = args.coqui

useCoqui:bool = True if coqui else False

if __name__ == "__main__":
    for model in AiModel.getAllModels():
        serverHost, ServerPort = model.getServerAddress()
        server = Server(host=serverHost,port=ServerPort,model=model, useCoqui= coqui)
        t = threading.Thread(target=server.serve, name='{} socket thread'.format(model.name))
        t.start()