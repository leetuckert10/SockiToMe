import socket
import json

from items import *

"""
This script is a simple socket client application that demonstrates how to pass a json serialized custom class
object over to the server. QueueItem is the wrapper class containing communication protocol fields and the
reference to another class that always part of the communication chunk. Serialization for the embedded class
reference does not work (at least as far as I delved into it) but you can simply add the fields from that embedded
class to QueueItem before it is serialized.
"""

HOST = 'localhost'
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

fubar = QueueItem(item=None, to_name="Carlee", from_name="Terry")
fubar.new_output = "Hey Carlee Blue!"
fubar.iteration_output = 4
fubar.testbed_output = True
fubar_as_dict = vars(fubar)
byte_str = json.dumps(fubar_as_dict)
s.sendall(byte_str.encode(encoding="utf-8"))

s.close()
print("Message sent to server...")


