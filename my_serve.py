import socket
import pickle

from items import *


HOST = 'localhost'
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print("Connected by", addr)

data = conn.recv(4096)
fubar = pickle.loads(data)      # This give the class back intact as the original QueueItem object.
conn.close()

print(fubar.print_data())
print(fubar.item.print_data())
