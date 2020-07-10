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
    """This is a static that is used to create a message to be sent either from SockServe or from
    ClientServe. The content dictionary can be modified as necessary to accommodate changing functionality
    requirements. I would not change anything else for fear of breaking messaging protocol (TLT)."""
    return dict(
        type="text/json",
        encoding="utf-8",
        content=dict(action=action,
                     iteration=iteration,
                     context=context,
                     value=value),
    )


class SockMessage:
    """This class defines and manages the message stack that is shared between SockServe and SockClient. The
    message stack defined here consists of the following:
    1.  A fixed length 2-byte header in big endian network format that gives the length of JSON header that
        follows.
    2.  Next is a serialized JSON header in Unicode text with UTF-8 encoding. The length of the JSON header
        is specified in the 2-byte integer header. The JSON header contains a dictionary of additional headers.
        One of those is content-length, which is the number of bytes of the message’s content (not including
        the JSON header).
    3.  Finally, we have the message content in the form of a dictionary. This we can modify to suit our needs.
        There several methods which manage this message stack that I did not write. They work perfectly.
    4.  This message stack enables us to have the right encoding for messages and more importantly, takes
        into account the byteorder of the machine on which it is running. Further, we are ensured that we are
        going to get the message in its entirety before we process it because we know how many bytes we are
        supposed to have.
    5.  Since reading the correct number of bytes and writing the correct number of bytes is imperative, this
        class manages all of the reading from and writing to the socket connection.

    All the SockServer connections to a client and all the clients connections to SockServer have an private
    instance of this class. Be careful when modifying any of the methods that begin with "_". (TLT)"""
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

    def initialize(self):
        """This method reinitialized various 'state' flags and message containers in between the sending
        and receiving of a message. It is called in process_message_in() and in _write()."""
        self._message_out_queued = False
        self._jsonheader_len = None
        self.jsonheader = None
        self.message_in = None
        self.message_out = None

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'. Currently, this method is not used
        since both communication points need to be able to read and write but please don't remove it (TLT)."""
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
        """This method simply reads up to 4096 bytes from the socket and appends it to the receive buffer.
        It is called by read()."""
        try:
            # Should be ready to read
            data = self._sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
        """I don't know yet if this needs to be deleted (TLT)."""
#           else:
#               raise RuntimeError("Peer closed.")

    def _write(self):
        """This method, if the send buffer is not empty, writes as many bytes to the socket as the socket will
        allow. Note that socket.send() returns the number on bytes written and that is leveraged to truncate the
        send buffer at the front end by the bytes written. If the transmission is incomplete for whatever reason,
        this method will be called again as soon as the socket is writeable and we simply pick up where we left
        off. Beautiful! Note that if the send buffer is empty at the end of this operation, we call initialize()
        to reset the world. (TLT)"""
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
                    self.initialize()

    def _json_encode(self, obj, encoding):
        """Apply the specified encoding to the JSON dictionary and shoot it back. Called by create_message_out()
        and queue_message_out()."""
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        """This method decodes the JSON bytes with the specified encoding. I have not studied the operation of
        io.TextIOWrapper(). This method is called by process_jsonheader() and process_message_in() (TLT)."""
        tiow = io.TextIOWrapper(io.BytesIO(json_bytes), encoding=encoding, newline="")
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message_out(self, *, content_bytes, content_type, content_encoding):
        """This method creates the JSON header, encodes it by calling _json_encode(), creates the fixed
        length beginning header, and finally, the content header. Note that it returns the stack as a
        'message'."""
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
        """This method is called by process_message_in(). This is the one place where we will be making
        modifications to an 'under bar' prefixed method. This has been modified to update the iteration and
        the context for this instance of SockMessage. Remember that SockServer does not know these values
        when it processes a connection request from a client and also remember that SockServer has its own
        instance of SockMessage on the other end of the communication link. Thus, if self.iteration is -1,
        then this is for sure the SockServer instance of SockMessage so we update the iteration and the
        context as well (TLT)."""
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
        """This method is called from process_message_in() when the content-type is not 'json/text'. I have
        not tested binary type messages (TLT)."""
        content = self.message_in
        print(f"got response: {repr(content)}")

    def process_events(self, mask):
        """This method is the entry point for SockMessage. The event loops in both SockServer and SockClient
        come in through the same door and this is it. Note that if message_out is None, then there is no
        point in worrying about a write operation. However, for a read operation, we have to actually do a
        read before we know if anything is there to deal with (TLT)."""
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE and self.message_out is not None:
            self.write()

    def read(self):
        """This method is called by process_events() on a read operation. The first thing we do is to actually
        read the socket calling _read(). If there is anything there to read, the receive buffer will be
        appended with the contents. If the read buffer is nothing, then we are through! Otherwise, we have some
        message headers to process."""
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
        """This method is called by process_events(). Remember that we do not even come here unless
        message_out is not None. If it is not None, then we have to queue the message if it has not been
        (remember that we may not have been able to send the whole message previously so it may have already
        been queued, but incomplete in transmission). Call _write() again or maybe, for the nth time."""
        if not self._message_out_queued:
            self.queue_message_out()

        self._write()

    def close(self):
        """This method is very well though out and it came with the Real Python source code, as much of this
        did. It does a superb job of shutting everything down (TLT)."""
        print("Closing connection to", self.addr)
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
        """This method is so cool! It is called by write() if the message has not already been "queued".
        It builds the communication stack by calling all those methods that build all the components. And
        when it is through, the send buffer has the complete message stored in it."""
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
        """This method is called by read(). It unpacks the first message header, sets the _jsonheader_len
        variable, and puts the rest of the message on the receive buffer."""
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(">H", self._recv_buffer[:hdrlen])[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        """This method is called by read(). The purpose now is to unpack the JSON header by using
        _jsonheader_len as determined by process_protoheader(). It validates the header by ensuring that
        the required keys are there otherwise, it raises a ValueError."""
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
        self.initialize()
        # Close when response has been processed
#       self.close()
