import zmq
import json

ZMQ_IFACE_EVENT = 'tcp://localhost:7779'

context = zmq.Context()
sub_socket = context.socket(zmq.SUB)
sub_socket.connect(ZMQ_IFACE_EVENT)
sub_socket.setsockopt(zmq.SUBSCRIBE, ''.encode())

while True:
    msg = sub_socket.recv_json()
    print('=====')
    print(json.dumps(msg, indent=4, sort_keys=True))
