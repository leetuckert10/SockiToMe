#!/usr/bin/python3

import socket

host = '127.0.0.1'  # server's host name / IP address
port = 65432        # this is the port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))         # connect
    s.sendall(b'Hello my Server!')  # send a message
    data = s.recv(1024)             # get a message back

# print("Received:", repr(data))
print("Received:", data.decode('utf-8'))
