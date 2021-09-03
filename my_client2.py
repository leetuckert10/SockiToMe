import socket
import json

from items import *


class Fubar:
    def __init__(self):
        self.process_id = 0


HOST = 'localhost'
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

# oi = OutputItem(new_output="This is a fubar!")
# fubar = QueueItem(item=None, to_name="Carlee", from_name="Terry")
fubar = QueueItem(item=None, to_name="terry", from_name="carlee")
fubar.process_id = 999999
fubar_as_dict = vars(fubar)
print(f">>>{fubar_as_dict}<<<")
byte_str = json.dumps(fubar_as_dict)
print(byte_str)
s.sendall(byte_str.encode(encoding="utf-8"))

s.close()
print("Message sent to server...")


