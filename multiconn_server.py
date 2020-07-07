#!/usr/bin/python3

import types
import socket
import selectors


def accept_wrapper(soc: socket.socket):
    conn, addr = soc.accept()
    print("Accepted connection from", addr)
    conn.setblocking(False)         # don't want this to block ignoring other connections
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events=events, data=data)


def service_connection(key: selectors.SelectorKey, mask:selectors.EVENT_READ | selectors.EVENT_WRITE):
    sock = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)     # Should be ready to read.
        if recv_data:
            data.outb += recv_data
        else:
            print("Closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print("Echoing", repr(data.outb), "to", data.addr)
            send = sock.send(data.outb)
            data.outb = data.outb[send:]


host = '127.0.0.1'  # standard loopback interface address (localhost)
port = 65432  # non-privileged ports are > 1023
sel = selectors.DefaultSelector()

listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listen_sock.bind((host, port))
listen_sock.listen()
listen_sock.setblocking(False)
print("Listening on", (host, port))

# Only interested in read events on the listening socket
sel.register(fileobj=listen_sock, events=selectors.EVENT_READ, data=None)

# Event loop
while True:
    events = sel.select(timeout=None)   # this blocks until there are sockets ready for I/O
    for key, mask in events:
        if key.data is None:        # then we know this is the listening socket
            accept_wrapper(key.fileobj)
        else:   # else, we know that this is a client that has already connected so service it
            service_connection(key, mask)
