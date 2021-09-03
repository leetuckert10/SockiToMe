#!/usr/bin/python3

import types
import socket
import selectors

messages = [b'Message 1 from client', b'Message 2 from client']
sel = selectors.DefaultSelector()


def start_connections(h, p, num):
    server_addr = (h, p)
    for i in range(0, num):
        connid = i + 1
        print("Starting connection", connid, "to", server_addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)

        """ connect_ex() is used instead of connect() since connect() would immediately raise a BlockingIOError
        exception. connect_ex() initially returns an error indicator, errno.EINPROGRESS, instead of raising an
        exception while the connection is in progress. """
        sock.connect_ex(server_addr)

        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        """It is very important to note that definition of this data is completely arbitrary."""
        data = types.SimpleNamespace(connid=connid,
                                     msg_total=sum(len(m) for m in messages),
                                     recv_total=0,
                                     messages=list(messages),
                                     outb=b'')
        sel.register(fileobj=sock, events=events, data=data)


def service_connection(key: selectors.SelectorKey, mask: selectors.EVENT_READ | selectors.EVENT_WRITE):
    sock = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)     # Should be ready to read.
        if recv_data:
            print(f"Received {recv_data.decode('utf-8')} from connection {data.connid}")
            data.recv_total += len(recv_data)   # Keep track of the total received as an exit point for client.

        if not recv_data or data.recv_total == data.msg_total:
            print(f"Closing connection {data.connid}")
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if not data.outb and data.messages:
            data.outb = data.messages.pop(0)

        if data.outb:
            print("Sending", data.outb.decode('utf-8'), "to", data.connid)
            send = sock.send(data.outb)
            data.outb = data.outb[send:]


def main():
    host = '127.0.0.1'  # standard loopback interface address (localhost)
    port = 65432  # non-privileged ports are > 1023
    number = 2

    start_connections(h=host, p=port, num=number)
    # Event loop
    try:
        while True:
            events = sel.select(timeout=None)   # this blocks until there are sockets ready for I/O
            for key, mask in events:
                service_connection(key, mask)
    except KeyboardInterrupt:
        exit(0)


if __name__ == "__main__":
    main()
