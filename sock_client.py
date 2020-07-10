#!/usr/bin/env python3

"""This code was adapted from a Real Python tutorial on Python socket programming.
It is available on Github (TLT)."""

import time
import socket
import threading
import traceback
from typing import Union

from sock_message import *


class SockClient:
    def __init__(self, host: str, port: int, iteration: int, context: str, testing: bool = False):
        self._host: str = host
        self._port: int = port
        self._iteration = iteration
        self._context = context
        self._testing = testing
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
                                   addr=server_addr,
                                   iteration=self._iteration,
                                   context=self._context)
        self._sel.register(sock, events, data=self.message)
        # Run the event loop in a thread when testing.
        if self._testing:
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


def main_test():
    if len(sys.argv) != 5:
        print("usage:", sys.argv[0], "<host> <port> <number connections>, context")
        sys.exit(1)

    host, port, num_conns, context = sys.argv[1:5]
    clients = []
    for x in range(0, int(num_conns)):
        iter = x + 1
        client = SockClient(host=host, port=int(port),
                            iteration=int(iter), testing=True,
                            context=context)
        clients.append(client)
        client.start_connection()
        time.sleep(1)
        client.message.message_out = create_message(action=SOCK_SET_ITERATION,
                                                    value=f"Hello my great SockServer from iteration {iter}!",
                                                    iteration=iter,
                                                    context=context)
        time.sleep(1)

    for client in clients:
        iter = client.message.iteration
        client.message.message_out = create_message(action=SOCK_STATUS,
                                                    value=f"Iteration {iter} is ready and waiting!!",
                                                    iteration=iter,
                                                    context=context)
        time.sleep(1)

    for client in clients:
        client.message.close()


def main():
    if len(sys.argv) != 5:
        print("usage:", sys.argv[0], "<host> <port> <iteration number> <context>")
        sys.exit(1)

    host, port, iteration, context = sys.argv[1:5]
    port = int(port)
    iteration = int(iteration)
    client = SockClient(host=host, port=int(port), iteration=iteration, context=context)
    client.start_connection()
    client.message.message_out = create_message(action=SOCK_SET_ITERATION,
                                                value=f"Hello my great SockServer from iteration {iteration}!",
                                                iteration=iteration,
                                                context = context)
    client.event_loop()


if __name__ == "__main__":
    main_test()
    # main_test()