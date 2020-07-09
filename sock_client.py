#!/usr/bin/env python3

import sys
import time
import types
import socket
import threading
import selectors
import traceback
from typing import Union

from sock_message import SockMessage, create_message


class SockClient:
    def __init__(self, host: str, port: int, iteration: int):
        self._host: str = host
        self._port: int = port
        self._iteration = iteration
        self._sel: selectors = selectors.DefaultSelector()
        self.message: Union[SockMessage, None] = None

    def start_connection(self):
        server_addr = (self._host, self._port)
        print("Starting connection to", server_addr)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex(server_addr)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.message = SockMessage(selector=self._sel, sock=sock,
                                   addr=server_addr, iteration=self._iteration)
        self._sel.register(sock, events, data=self.message)
        # Run the event loop in a thread.
        threading.Thread(target=self.event_loop, daemon=True).start()

    def event_loop(self):
        try:
            while True:
                events = self._sel.select(timeout=1)
                for key, mask in events:
                    print("Client in for loop")
                    message: SockMessage = key.data
                    try:
                        message.process_events(mask)
                    except Exception:
                        print("main: error: exception for",
                              f"{message.addr}:\n{traceback.format_exc()}")
                        message.close()
                # Check for a socket being monitored to continue.
                if not self._sel.get_map():
                    break
                time.sleep(1)
        except KeyboardInterrupt:
            print("Caught keyboard interrupt, exiting")
        finally:
            self._sel.close()


def main():
    if len(sys.argv) != 4:
        print("usage:", sys.argv[0], "<host> <port> <iteration number>")
        sys.exit(1)

    host, port, num_conns = sys.argv[1:4]
    clients = []
    for x in range(0, int(num_conns)):
        iter = x + 1
        client = SockClient(host=host, port=int(port), iteration=iter)
        clients.append(client)
        client.start_connection()
        time.sleep(2)
        client.message.message_out = create_message(action="command",
                                                    value=f"Hello my great Server from connection {iter}!",
                                                    iteration=iter)
        time.sleep(2)

    for client in clients:
        client.message.close()


if __name__ == "__main__":
    main()