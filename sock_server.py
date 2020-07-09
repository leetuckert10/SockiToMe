#!/usr/bin/env python3

import sys
import time
import socket
import selectors
import threading
import traceback

from typing import Union, List


from sock_message import SockMessage, create_message


class SockServer:
    def __init__(self, my_host: str, my_port: int):
        self._host:str = my_host
        self._port: int = my_port
        self._listen_sock = None
        self._sel: selectors = selectors.DefaultSelector()

        self.connections: List = []

    def setup_listen_socket(self):
        self._listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Avoid bind() exception: OSError: [Errno 48] Address already in use
        self._listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._listen_sock.bind((self._host, self._port))
        self._listen_sock.listen()
        print("Listening on", (self._host, self._port))
        self._listen_sock.setblocking(False)
        self._sel.register(self._listen_sock, selectors.EVENT_READ, data=None)

        # Start the event loop in a thread.
        threading.Thread(target=self.event_loop, daemon=True).start()

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        print("Accepted connection from", addr)
        conn.setblocking(False)
        message = SockMessage(self._sel, sock=conn, addr=addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self._sel.register(conn, events, data=message)
        self.connections.append(message)

    def close(self):
        self._sel.close()

    def event_loop(self):
        try:
            while True:
                events = self._sel.select(timeout=None)
                for key, mask in events:
                    print("Server in for loop")
                    if key.data is None:
                        self.accept_wrapper(key.fileobj)
                    else:
                        message: SockMessage = key.data
                        try:
                            message.process_events(mask)
                        except Exception:
                            print("Server: error: exception for",
                                  f"{message.addr}:\n{traceback.format_exc()}")
                            message.close()
                time.sleep(1)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting...")
        finally:
            self._sel.close()


def main():
    if len(sys.argv) != 3:
        print("usage:", sys.argv[0], "<host> <port>")
        sys.exit(1)

    host, port = sys.argv[1], int(sys.argv[2])
    server = SockServer(host, port)
    server.setup_listen_socket()
    time.sleep(10)
    server.connections[0].message_out = create_message(action="command",
                                                       value=f"Ready to pump that pussy baby!!")
    time.sleep(50)
    server.close()


if __name__ == "__main__":
    main()
