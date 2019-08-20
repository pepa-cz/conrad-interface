import time
import json
import logging
from datetime import datetime
from telnetlib import Telnet
from multiprocessing import Queue, Process, Manager
import zmq

# FHEM configuration
FHEM_HOST = 'fhem'
FHEM_PORT = 7072
READ_TIMEOUT = 0.5
TN_TIMEOUT = 1

# ZMQ configuration
ZMQ_IFACE_CMD = 'tcp://*:7778'    # command REQ-REP interface
ZMQ_IFACE_EVENT = 'tcp://*:7779'  # event PUB-SUB interface

# shared dictionary
sd = Manager().dict()
# init logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)
# telnet queues
tn_req = Queue()
tn_rsp = Queue()


def tn_loop():
    initialized = False

    while True:
        cmd = tn_req.get()
        if not initialized:
            try:
                tn = Telnet(FHEM_HOST, FHEM_PORT, TN_TIMEOUT)
            except Exception as e:
                log.error('Cannot init telnet connection: ' + str(e))
                tn_rsp.put(None)
                time.sleep(2)
                continue
            initialized = True

        try:
            tn.write((cmd + '\n').encode())
            time.sleep(READ_TIMEOUT)
            ret = tn.read_very_eager()
            #print(ret)
        except Exception as e:
            log.error('Cannot query data: ' + str(e))
            tn_rsp.put(None)
            initialized = False
            continue

        tn_rsp.put(ret.decode())


def pair(seconds):
    log.info('Pair mode started for %d seconds' % seconds)
    tn_req.put('set CUL_0 hmPairForSec %d' % seconds)
    return tn_rsp.get()


def unpair(device):
    tn_req.put('delete HM_' + device)
    tn_rsp.get()


def status():
    tn_req.put('jsonlist2')
    ret = tn_rsp.get()

    ret = json.loads(ret)
    rsp = {}
    for i in ret['Results']:
        if 'Name' not in i:
            continue

        if not i['Name'].startswith('HM'):
            continue

        dev = i['Name'].split('_')
        if dev[1] not in rsp:
            rsp[dev[1]] = {'rssi': None,
                           'msg_cnt': None,
                           'channels': {},
                           'last_rcv_ts': None,
                           'last_rcv': None,
                           'rcv_cnt': 0,
                           'resnd_cnt': 0,
                           'snd_cnt': 0}

        if len(dev) == 2:
            rsp[dev[1]]['rssi'] = i['Internals'].get('CUL_0_RSSI',)
            rsp[dev[1]]['msg_cnt'] = int(i['Internals'].get('CUL_0_MSGCNT', 0))

            if i['Internals'].get('CUL_0_RAWMSG', None) is None:
                rsp[dev[1]]['payload'] = None
            else:
                rsp[dev[1]]['payload'] = i['Internals']['CUL_0_RAWMSG'].split(':')[0]

            rsp[dev[1]]['prot_state'] = i['Internals'].get('protState', None)

            if 'protRcv' in i['Internals']:
                rsp[dev[1]]['rcv_cnt'] = int(i['Internals']['protRcv'].split()[0])
            if 'protResnd' in i['Internals']:
                rsp[dev[1]]['resnd_cnt'] = int(i['Internals']['protResnd'].split()[0])
            if 'protSnd' in i['Internals']:
                rsp[dev[1]]['snd_cnt'] = int(i['Internals']['protSnd'].split()[0])

            rsp[dev[1]]['last_rcv'] = i['Internals'].get('protLastRcv', None)
            if rsp[dev[1]]['last_rcv'] is not None:
                rsp[dev[1]]['last_rcv_ts'] = datetime.strptime(rsp[dev[1]]['last_rcv'], '%Y-%m-%y %H:%M:%S').timestamp()

            if 'STATE' in i['Internals']:
                rsp[dev[1]]['channels']['Main'] = i['Internals']['STATE']

            rsp[dev[1]]['model'] = i['Attributes']['model']
            rsp[dev[1]]['type'] = i['Attributes']['subType']
            rsp[dev[1]]['serial'] = i['Attributes']['serialNr']

        if len(dev) == 3:
            rsp[dev[1]]['channels'][dev[2]] = {}
            rsp[dev[1]]['channels'][dev[2]]['state'] = i['Internals']['STATE']

            #print(json.dumps(i, indent=4, sort_keys=True))
    #print(json.dumps(rsp, indent=4, sort_keys=True))
    return(rsp)


def detect_event(pub_socket):

    if sd['status_old'] is None:
        sd['status_old'] = sd['status']
        return None

    for dev, stat in sd['status'].items():
        if dev not in sd['status_old']:
            pub_socket.send_json({
                'event': 'new_device',
                'dev': dev,
                'type': stat['type'],
                'serial': stat['serial'],
                'model': stat['model'],
            })
            continue

        stat_old = sd['status_old'][dev]

        # new message from device
        if stat['last_rcv_ts'] != stat_old['last_rcv_ts']:

            pub_socket.send_json({
                'event': 'message',
                'raw': stat['payload'],
                'rssi': float(stat['rssi']),
                'channels': stat['channels'],
                'dev': dev,
                'type': stat['type']
            })

        for i in ['snd_cnt', 'resnd_cnt', 'rcv_cnt', 'prot_state']:
            if stat_old[i] != stat[i]:
                pub_socket.send_json({
                    'event': i,
                    'dev': dev
                })

    sd['status_old'] = sd['status']
    return


def zmq_loop_cmd():
    # create REQ-REP interface
    context = zmq.Context.instance()
    rep_socket = context.socket(zmq.REP)
    rep_socket.bind(ZMQ_IFACE_CMD)

    while True:
        resp = {}
        msg = rep_socket.recv_json()
        if 'cmd' not in msg:
            continue
        elif msg['cmd'] == 'status':
            resp = sd['status']
        elif msg['cmd'] == 'pair':
            pair(msg.get('tout', 60))
        elif msg['cmd'] == 'unpair':
            unpair(msg.get('device', 'ABCD'))

        #print(msg)
        #resp = {'RSP': 'B'}
        #resp = status()
        rep_socket.send_json(resp)


def zmq_loop_event():
    # create PUB-SUB interface
    context = zmq.Context()
    pub_socket = context.socket(zmq.PUB)
    pub_socket.bind(ZMQ_IFACE_EVENT)

    while True:
        detect_event(pub_socket)
        time.sleep(1)


Process(target=tn_loop).start()
Process(target=zmq_loop_cmd).start()
Process(target=zmq_loop_event).start()

#pair(60)

sd['status_old'] = None
sd['status'] = None
while True:
    try:
        sd['status'] = status()
    except Exception as e:
        log.error('Cannot read status: ' + str(e))

    # process and send events
    pass
