from __future__ import print_function
import socket
import sys
import threading
import packet_wrapper
import random
import pickle
import time
import logging
import ConfigParser


class Socket(object):
    def __init__(self, port):
        """
        Init

        Server object initialization
        :param port:
        :return:
        """

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # create a file handler
        handler = logging.FileHandler('channel.log')
        handler.setLevel(logging.INFO)

        # Consume the configuration file
        self.config = ConfigParser.RawConfigParser()
        self.config.read('config.ini')

        # add the handlers to the logger
        self.logger.addHandler(handler)

        self.hostname = ""
        self.port_send = int(port)
        self.port_recv = int(port)+1
        self.buffsize = 1024
        self.socket_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_recv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.socket_file = self.socket.makefile("rb")
        self.direction = "put"

    def producer(self, queue):

        # Bind to socket
        self.logger.info("Transmitter: Bound to port {}".format(self.port_recv))
        self.logger.info("Transmitter:  Connected to port {}".format(self.port_send))
        self.socket_recv.bind((self.hostname, self.port_recv))
        self.socket_send.connect((self.hostname, self.port_send))

        # Start listener
        self.logger.info("Transmitter: Server listening...")

        # Maintain infinite loop to accept connections
        while True:
            if self.direction == "put":
                self.logger.info("Transmitter: Set as Intake from Socket -> Queue")
                # Wait to accept connections with blocking call
                # conn, address = self.socket.accept()
                data, address = self.socket_recv.recvfrom(self.buffsize)

                data_obj = pickle.loads(data)
                queue.maxsize = int(data_obj.window_size) + 1

                # packet type set as 0 for EOT
                if data_obj.packet_type == 0:
                    self.direction = "get"
                    self.logger.info("Transmitter: Server received EOT from transmitter. Ending.")
                    queue.put(data)
                    time.sleep(0.3)
                    continue

                # Receive data from client
                self.logger.info("Transmitter: Server received data: '{0}' Putting into queue...".format(data_obj.__dict__))

                # Introduce random noise (dropped packets)
                rand_num = random.random()
                if rand_num < float(self.config.get('channel', 'noise_percent_loss')):
                    self.logger.info("Receiver: {} < {} - Packet Dropped...".format(rand_num, self.config.get('channel',
                                                                                                              'noise_percent_loss')))
                    continue

                # Put data into the queue
                queue.put(data)
            else:
                self.logger.info("Transmitter: Set as Intake from Queue -> Socket")
                # Receive data from the queue
                packets = queue.get()

                # Receive data from client
                self.logger.info("Transmitter: Pulled data from queue, sending to producer...")

                packet = pickle.loads(packets)
                if packet.packet_type == 0:
                    self.direction = "put"

                self.socket_send.send(packets)

        self.socket.close()

    def consumer(self, queue):

        # Bind to socket
        self.logger.info("Receiver: Bound to port {}".format(self.port_recv))
        self.logger.info("Receiver: Connected to port {}".format(self.port_recv+1))
        self.socket_recv.bind((self.hostname, self.port_recv))
        self.socket_send.connect((self.hostname, self.port_recv+1))

        # Start listener
        self.logger.info("Receiver: Server listening...")

        # Maintain infinite loop to accept connections
        while True:
            if self.direction == "put":
                self.logger.info("Receiver: Set as Intake from Queue -> Socket")
                # Receive data from the queue
                packets = queue.get()

                # Wait to accept connections with blocking call
                # conn, address = self.socket.accept()
                # Receive data from client
                self.logger.info("Receiver: Pulled data from queue, sending to receiver...")

                packet = pickle.loads(packets)
                if packet.packet_type == 0:
                    self.direction = "get"

                self.socket_send.send(packets)

            else:
                self.logger.info("Receiver: Set as Intake from Socket -> Queue")
                # Wait to accept connections with blocking call
                # conn, address = self.socket.accept()
                data, address = self.socket_recv.recvfrom(self.buffsize)

                data_obj = pickle.loads(data)

                # packet type set as 0 for EOT
                if data_obj.packet_type == 0:
                    self.direction = "put"
                    self.logger.info("Receiver: Server received EOT from receiver. Ending.")
                    queue.put(data)
                    time.sleep(0.3)
                    continue

                # Receive data from client
                self.logger.info("Receiver: Server received data: '{0}' Putting into queue...".format(data_obj.__dict__))

                # Introduce random noise (dropped packets)
                rand_num = random.random()
                if rand_num < float(self.config.get('channel', 'noise_percent_loss')):
                    self.logger.info("Receiver: {} < {} - Packet Dropped...".format(rand_num, self.config.get('channel', 'noise_percent_loss')))
                    continue

                # Put data into the queue
                queue.put(data)

        self.socket.close()
