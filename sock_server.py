#!/usr/bin/env python3

"""This code was adapted from a Real Python tutorial on Python socket programming.
It is available on Github (TLT)."""

import time
import socket
import threading
import traceback

from typing import List


from sock_message import *


class SockServer:
    """This class is the socket server that provides a communication link between select VMs running
    as part of a test iteration. It is designed to handle multiple connections from the client software.
    It should be instantiated from the testbed. The event loop runs in a thread."""
    def __init__(self, my_host: str, my_port: int, context: str = None):
        self._host: str = my_host
        self._port: int = my_port
        self._context: str = context
        self._listen_sock = None
        self._sel: selectors = selectors.DefaultSelector()

        self.sock_objects: List[SockMessage] = []

    def setup_listen_socket(self):
        """This method sets up the listening socket. For each connection, the listening socket will be
        cloned by socket.accept()."""
        self._listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Avoid bind() exception: OSError: [Errno 48] Address already in use.
        self._listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._listen_sock.bind((self._host, self._port))
        self._listen_sock.listen()
        self._listen_sock.setblocking(False)
        print("Listening on", (self._host, self._port))

        # Register the socket with selectors API.
        self._sel.register(self._listen_sock, selectors.EVENT_READ, data=None)

        # Start the event loop in a thread.
        threading.Thread(target=self.event_loop, daemon=True).start()

    def accept_wrapper(self, sock):
        """This method is called from the event loop and establishes a connection in answer to a request
        for a connection. It keeps a list of SockMessage instance references so messages can be sent to
        clients with a specific iteration and context."""
        conn, addr = sock.accept()  # Clones the listening socket for the server end on the connection.
        print("Accepted connection from", addr)
        conn.setblocking(False)
        """Keep in mind that the SockMessage instance that is created here is on the server side of the
        connection! The client connection has its own instance of SockMessage."""
        sock_message = SockMessage(self._sel, sock=conn, addr=addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._sel.register(conn, events, data=sock_message)
        self.sock_objects.append(sock_message)

    def close(self):
        """We make the assumption that the client on the other end is going to close itself up when through."""
        self._sel.close()

    def send_message(self, action: str, iteration: int, context: str, message: str):
        """When the server needs to send a message to a client, we need to find which client to send it
        to based on the iteration number and the client context."""
        for sock_object in self.sock_objects:       # Our list of SockMessage client connections.
            if sock_object.iteration == iteration and sock_object.context == context:
                sock_object.message_out = create_message(action=action, value=message, iteration=iteration)
                break

    def event_loop(self):
        """This is the event loop for monitoring socket connections. We are using select() which returns a list
        of socket connections that are ready for I/O. key.fileobj is the socket. key.data is a reference to
        SockMessage. If key.data is None, then this is the listening socket and so we call accept_wrapper()
        otherwise, we call sock_obj.process_events() passing in the communication type mask."""
        try:
            while True:
                events = self._sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        sock_object: SockMessage = key.data
                        try:
                            sock_object.process_events(mask)
                        except Exception:
                            print("Server: error: exception for",
                                  f"{sock_object.addr}:\n{traceback.format_exc()}")
                            sock_object.close()
                time.sleep(1)   # just pausing for a second to keep from breaking the speed limit ;)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting...")
        finally:
            self._sel.close()


def main():
    """This function is for commandline testing only. As part of the testbed the SockServer class will be
    instantiated by Testbed and the event loop will run in a thread."""
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)

    host, port = sys.argv[1], int(sys.argv[2])
    server = SockServer(host, port)
    server.setup_listen_socket()
    time.sleep(20)

    # Just a sample message for testing.
    server.send_message(action=SOCK_STATUS, iteration=5,
                        context=SOCK_CONTEXT_ATTACK,
                        message="Ready, Aim, FIIIIIIRE!!!")

    time.sleep(50)
    server.close()


if __name__ == "__main__":
    main()
