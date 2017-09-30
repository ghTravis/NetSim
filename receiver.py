#!/usr/bin/env python

from __future__ import print_function
from random import randint
from lib import socket_wrapper as SWrapper
from lib import packet_wrapper as PWrapper
import ConfigParser
import sys
import socket
import pickle
import time
import logging


class Receiver(object):
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
        handler = logging.FileHandler('receiver.log')
        handler.setLevel(logging.INFO)

        # add the handlers to the logger
        self.logger.addHandler(handler)

        # Consume the configuration file
        self.config = ConfigParser.RawConfigParser()
        self.config.read('config.ini')

        self.port = int(self.config.get('receiver', 'port'))
        self.host = self.config.get('receiver', 'host')

        self.bufsize = 1024
        self.socket_send = SWrapper.Socket(port=self.port-1)
        self.socket_recv = SWrapper.Socket(port=self.port)

        self.packet_list = []

        # Connect to a remote host by opening a socket for communication
        self.logger.info("Bound to port {}".format(self.port))
        self.logger.info("Connected to port {}".format(self.port-1))
        self.socket_send.socket_send.connect((self.host, self.port-1))
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

            # Get data from the receive socket
            data, address = self.socket_recv.socket_recv.recvfrom(self.bufsize)
            data_obj = pickle.loads(data)

            if data_obj.packet_type == 2:
                continue

            # Add all packets to the packet_list
            self.packet_list.append(int(data_obj.sequence_number))

            # Check packet type for EOT packet (0) and begin sending ACKs back
            # Clear the packet list for the next set of packets
            self.logger.info("Received type {} packet with sequence number {} from server: {}".format(data_obj.packet_type, data_obj.sequence_number, data_obj.payload))
            if data_obj.packet_type == 0:
                self.send_ack()
                self.packet_list = []
                continue

        self.socket_send.socket_send.close()
        self.socket_recv.socket_recv.close()

    def send_ack(self):
        """
        send_ack

        Send ACKs back to the channel for every incoming data and eot packet received.

        :return:
        """
        # Begin the next sequence number at the last packet +1
        sequence_num = self.packet_list[-1]+1

        # Begin ACKing packets in the packet_list
        for packet in self.packet_list:

            # Build the ACK packet (2)
            # Packet sequence number will be the last packet in the received list + 1
            # packet ACK number will be whatever packet number is in the list, remove that packet from the list after processing
            self.logger.info("Processing packet, ACKing packet {} with sequence number {}".format(packet, sequence_num))
            ack = PWrapper.Packet(2, sequence_num, "", None, packet)
            ack = pickle.dumps(ack)

            # Send the packet to the send socket, increment the sequence number
            self.socket_send.socket_send.send(ack)
            sequence_num += 1

        # Send the EOT packet
        self.logger.info("Sending EOT packet with sequence number {}".format(sequence_num))
        eot = PWrapper.Packet(0, sequence_num, "", None)
        eot = pickle.dumps(eot)
        self.socket_send.socket_send.send(eot)


if __name__ == "__main__":

    # Initialize the Server Object

    # Call send(), handle errors and close socket if exception
    try:
        run = Receiver()
        run.main()

    except KeyboardInterrupt as e:
        run.socket_send.socket_send.close()
        run.socket_recv.socket_send.close()
        exit()
