import socket
import json

from items import *


"""
This is the server script for my_client2. See the documentation in that script.
"""

HOST = 'localhost'
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print("Connected by", addr)

data = conn.recv(4096)
data_str = data.decode(encoding="utf-8")
fubar = json.loads(data_str)
conn.close()

print(fubar)
