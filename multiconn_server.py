#!/usr/bin/python3

import types
import socket
import selectors


def accept_wrapper(soc: socket.socket):
    conn, addr = soc.accept()
    print("Accepted connection from", addr)
    conn.setblocking(False)         # don't want this to block ignoring other connections
    # We define an object for holding the data we want included with the new connection.
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    # Register this new connection for read and write.
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    # New connection is ready for communication.
    sel.register(conn, events=events, data=data)


def service_connection(key: selectors.SelectorKey, mask: selectors.EVENT_READ | selectors.EVENT_WRITE):
    sock = key.fileobj          # key is an object that contains the socket object and the data object.
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)     # Should be ready to read.
        if recv_data:
            data.outb += recv_data      # appending the data so we can send it later.
        else:
            """ If we get a read event from the client but there is no data read, then we know that the
            client has closed the connection so we do the same on our end and unregister the socket so 
            that it is no longer monitored by select(). """
            print("Closing connection to", data.addr)
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if data.outb:
            print("Echoing", repr(data.outb), "to", data.addr)
            """ send() returns the number of bytes sent. We use that value to slice the data that was
            sent out of the outb buffer. """
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

"""
Only interested in read events on the listening socket. sel.register registers the socket for monitoring
by sel.select(). We use data to keep trick of what has be sent and received on the socket.
"""
sel.register(fileobj=listen_sock, events=selectors.EVENT_READ, data=None)

# Event loop
while True:
    """ sel.select() blocks until there are sockets ready for I/O. It returns a list of (key, events) tuples,
    one for each socket. key is a SelectorKey namedtuple that contains a fileobj attribute. key.fileobj is
    the socket object, and mask is an event mask of the operations that are ready. """
    event = sel.select(timeout=None)
    for key, mask in event:
        print(f"{key}, {mask}")
        if key.data is None:        # then we know this is the listening socket
            accept_wrapper(key.fileobj)
        else:                       # else, we know that this is a client that has already connected so service it
            service_connection(key, mask)
