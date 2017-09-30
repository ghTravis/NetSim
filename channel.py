#!/usr/bin/env python
from lib import socket_wrapper as Wrapper
from multiprocessing import Queue
from threading import Thread

import sys
import ConfigParser


if __name__ == "__main__":

    # Consume the configuration file
    config = ConfigParser.RawConfigParser()
    config.read('config.ini')

    # Initialize the Server Object
    ingress = Wrapper.Socket(port=config.get('channel', 'ingress_port'))
    egress = Wrapper.Socket(port=config.get('channel', 'egress_port'))

    # Call send(), handle errors and close socket if exception
    try:
        q = Queue()
        t1 = Thread(target=ingress.producer, args=(q,))
        t2 = Thread(target=egress.consumer, args=(q,))

        t1.start()
        t2.start()

    except (KeyboardInterrupt, SystemExit) as e:
        sys.exit()
