from socket import *
from threading import Thread


sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(("localhost", 8888))
sock.listen(10)
sock.setblocking(False)

def handle_data():
    ...


