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

sp = SubprocessItem(for_node="snot", argument_list=["b", "r", "5", "4", "9"], command_str="del all", action="boom",
                    context="my ass")
qi = QueueItem(item=sp, to_name="SockServ", from_name="YoMamma")
item = qi.item
qi.item = None

qi_as_dict = vars(qi)
item_as_dict = vars(item)
merged = {**qi_as_dict, **item_as_dict}
qi.item = item

byte_str = json.dumps(merged)
s.sendall(byte_str.encode(encoding="utf-8"))

s.close()
print("Message sent to server...")


