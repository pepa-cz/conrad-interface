FROM python:rc-buster

RUN apt-get update && \
    apt-get install -y libczmq-dev && \
    pip3 install zmq
