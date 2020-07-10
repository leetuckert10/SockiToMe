"""This code was adapted from a Real Python tutorial on Python socket programming.
It is available on Github (TLT)."""

import sys
import selectors
import json
import io
import struct

# Socket communication command and context strings.
SOCK_SET_ITERATION = "set_iteration"
SOCK_STATUS = "status"
SOCK_CONTEXT_ATTACK = "attack"
SOCK_CONTEXT_MEASUREMENTS = "measurements"
SOCK_COMMAND = "command"


def create_message(action, value: str, iteration: int = -1, context: str = SOCK_STATUS):
    return dict(
        type="text/json",
        encoding="utf-8",
        content=dict(action=action, iteration=iteration, context=context, value=value),
    )


class SockMessage:
    def __init__(self, selector, sock, addr, context: str = None, iteration: int = -1):
        self._selector = selector
        self._sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""
        self._message_out_queued = False
        self._jsonheader_len = None

        self.jsonheader = None
        self.context: str = context
        self.iteration: int = iteration
        self.message_in = None
        self.message_out = None

    def initiaize(self):
        self._message_out_queued = False
        self._jsonheader_len = None
        self.jsonheader = None
        self.message_in = None
        self.message_out = None

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self._selector.modify(self._sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self._sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
#           else:
#               raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            print("Sending", repr(self._send_buffer), "to", self.addr)
            try:
                # Should be ready to write
                sent = self._sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]
                if self._send_buffer == b"":
                    self.initiaize()

    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(io.BytesIO(json_bytes), encoding=encoding, newline="")
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message_out(self, *, content_bytes, content_type, content_encoding):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def _process_message_in_json_content(self):
        content = self.message_in
        action = content.get("action")
        message = content.get("value")
        context = content.get("context")
        iteration = content.get("iteration")
        if self.iteration == -1 and action == SOCK_SET_ITERATION:
            self.iteration = iteration
            self.context = context
        print(f"Iteration {self.iteration} got message: {message}...")

    def _process_message_in_binary_content(self):
        content = self.message_in
        print(f"got response: {repr(content)}")

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE and self.message_out is not None:
            self.write()

    def read(self):
        self._read()

        if not self._recv_buffer:
            return

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_jsonheader()

        if self.jsonheader:
            if self.message_in is None:
                self.process_message_in()

    def write(self):
        if not self._message_out_queued:
            self.queue_message_out()

        self._write()

        # if self._message_out_queued:
            # if not self._send_buffer:
                # Set selector to listen for read events, we're done writing.
                # self._set_selector_events_mask("r")

    def close(self):
        print("closing connection to", self.addr)
        try:
            self._selector.unregister(self._sock)
        except Exception as e:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self._sock.close()
        except OSError as e:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self._sock = None

    def queue_message_out(self):
        content = self.message_out["content"]
        content_type = self.message_out["type"]
        content_encoding = self.message_out["encoding"]
        if content_type == "text/json":
            req = {
                "content_bytes": self._json_encode(content, content_encoding),
                "content_type": content_type,
                "content_encoding": content_encoding,
            }
        else:
            req = {
                "content_bytes": content,
                "content_type": content_type,
                "content_encoding": content_encoding,
            }
        message = self._create_message_out(**req)
        self._send_buffer += message
        self._message_out_queued = True

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(">H", self._recv_buffer[:hdrlen])[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(self._recv_buffer[:hdrlen], "utf-8")
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                    "byteorder",
                    "content-length",
                    "content-type",
                    "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

    def process_message_in(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.message_in = self._json_decode(data, encoding)
            print("Message received", repr(self.message_in), "from", self.addr)
            self._process_message_in_json_content()
        else:
            # Binary or unknown content-type
            self.message_in = data
            print(f'Binary data received {self.jsonheader["content-type"]} response from', self.addr)
            self._process_message_in_binary_content()
        self.initiaize()
        # Close when response has been processed
#       self.close()
