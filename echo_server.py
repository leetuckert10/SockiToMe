#!/usr/bin/python3

import socket

host = '127.0.0.1'  # standard loopback interface address (localhost)
port = 65432  # non-privileged ports are > 1023

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((host, port))
    s.listen()  # this blocks waiting for a connection
    conn, addr = s.accept()  # this returns a new socket connection
    with conn:
        print('Connected by', addr)
        while True:
            data = conn.recv(1024)  # a blocking operation that receives at most 1024 bytes at one time
            # conn.recv returns a bytes object

            if not data:
                break

            # sendall() sends all of the data back to the client. Returns None on success.
            conn.sendall(data)
