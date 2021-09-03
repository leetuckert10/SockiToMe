import socket
import pickle

from items import *

HOST = 'localhost'
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

oi = OutputItem(new_output="This is a fubar!")
fubar = QueueItem(item=oi, to_name="Carlee", from_name="Terry")
byte_str = pickle.dumps(fubar)
s.send(byte_str)

s.close()
print("Message sent to server...")


