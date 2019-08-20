import zmq
import json

ZMQ_IFACE_CMD = 'tcp://localhost:7778'
PAIR_MSG = {'cmd': 'pair', 'tout': 20}

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(ZMQ_IFACE_CMD)
socket.send_json(PAIR_MSG)
rsp = socket.recv_json()
print(json.dumps(rsp, indent=4, sort_keys=True))
