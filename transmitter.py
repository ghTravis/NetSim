#!/usr/bin/env python

from __future__ import print_function
from random import randint
from lib import socket_wrapper as SWrapper
from lib import packet_wrapper as PWrapper
from threading import Timer
import sys
import socket
import time
import pickle
import ConfigParser
import logging


class Transmitter(object):
    """
    Client Class

    Establish connection with server and download a file
    """

    def __init__(self):
        """
        Init

        Client object initialization
        :param host:
        :param port:
        :return:
        """

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # create a file handler
        handler = logging.FileHandler('transmitter.log')
        handler.setLevel(logging.INFO)

        # add the handlers to the logger
        self.logger.addHandler(handler)

        # Consume the configuration file
        self.config = ConfigParser.RawConfigParser()
        self.config.read('config.ini')

        self.port = int(self.config.get('transmitter', 'port'))
        self.host = self.config.get('transmitter', 'host')

        self.bufsize = 1024
        self.socket_send = SWrapper.Socket(port=self.port+1)
        self.socket_recv = SWrapper.Socket(port=self.port)
        self.packets = None
        self.rate = None
        self.sequence_num = 0
        self.timer = None

        # Connect to a remote host by opening a socket for communication
        self.logger.info("Bound to port {}".format(self.port))
        self.logger.info("Connected to port {}".format(self.port+1))
        self.socket_send.socket_send.connect((self.host, self.port+1))
        self.socket_recv.socket_recv.bind(("", self.port))

    def main(self):
        """
        main

        Send a command to a server for file transfer actions
        :param command:
        :param filename:
        :return:
        """

        # Maintain continuous loop
        while True:

            # Loop through window size of self.packets -1 (EOT packet always at the end)
            # Keep a list of packets we need to be ACK'd
            packet_list = []
            packet_list = self.transmit()

            # Wait for the packets to come back ACK'd, and for a final EOT packet
            while len(packet_list)+1 > 0:

                # Get data from the receive socket
                data, address = self.socket_recv.socket_recv.recvfrom(self.bufsize)
                data_obj = pickle.loads(data)

                if data_obj.packet_type == 0:
                    self.logger.info("Received EOT packet with sequence number {}".format(data_obj.sequence_number))
                    #self.timer.cancel()

                    if len(packet_list) > 0:
                        time.sleep(self.rate)
                        self.logger.info("Packet list not empty, trying retransmit of packets: {}...".format(packet_list))
                        self.transmit(packet_list, force=True)
                        continue

                    self.sequence_num = data_obj.sequence_number+1
                    break

                # We don't want any packet that isn't of type ACK (2) or EOT
                if data_obj.packet_type != 2:
                    continue

                # Continue if the packet we receive does not have an ACK number
                try:
                    packet_list.remove(data_obj.ack_num)
                except ValueError as e:
                    continue

                self.logger.info("Received type {} packet with sequence number {} from server: {}".format(data_obj.packet_type,
                                                                                               data_obj.sequence_number,
                                                                                               data_obj.payload))
                self.logger.info("removing sequence number {} from packet_list, packets still remaining: {}".format(data_obj.ack_num, packet_list))


        self.socket_send.socket_send.close()
        self.socket_recv.socket_recv.close()

    def transmit(self, packet_list=[], force=False):

        if force == True:
            for x in packet_list:
                # Create data packet and add to the packet_list
                packet = PWrapper.Packet(1, x, "a", len(packet_list)+1)
                #packet_list.append(self.sequence_num)

                # Send packet to the sending socket, serialize the packet object with pickle
                self.socket_send.socket_send.send(pickle.dumps(packet))

        else:
            x = 0
            while x < int(self.packets) - 1:
                # Create data packet and add to the packet_list
                packet = PWrapper.Packet(1, self.sequence_num, "a", int(self.packets))
                packet_list.append(self.sequence_num)

                # Send packet to the sending socket, serialize the packet object with pickle
                self.socket_send.socket_send.send(pickle.dumps(packet))

                # Increment the counter and sequence number
                x += 1
                self.sequence_num += 1

        # append the EOT packet to the end, increment the sequence number, send it to the channel
        time.sleep(self.rate)
        packet = PWrapper.Packet(0, self.sequence_num, "", int(self.packets))
        packet_list.append(self.sequence_num)
        self.sequence_num += 1
        self.socket_send.socket_send.send(pickle.dumps(packet))

        # self.timer = Timer(3, self.timeout(packet_list))
        # self.timer.start()

        self.logger.info(packet_list)
        return packet_list

    def timeout(self, packet_list):
        print("Timed out while waiting for packets...")
        self.transmit(packet_list)


if __name__ == "__main__":

    # Initialize the Server Object

    packets = sys.argv[1]
    rate = float(sys.argv[2])

    # Call send(), handle errors and close socket if exception
    try:
        run = Transmitter()
        run.packets = packets
        run.rate = float(rate)
        run.main()

    except KeyboardInterrupt as e:
        run.socket_send.socket_send.close()
        run.socket_recv.socket_recv.close()
        exit()
