from __future__ import print_function
import socket
import sys
import threading


class Packet(object):
    def __init__(self, packet_type, sequence_number, payload, window_size, ack_num=None):
        """

        Packet_Type     0 = EOT
                        1 = Data
                        2 = ACK

        :param packet_type:
        :param sequence_number:
        :param payload:
        :param window_size:
        :param ack_num:
        """
        self.packet_type = packet_type
        self.sequence_number = sequence_number
        self.payload = payload
        self.window_size = window_size
        self.ack_num = ack_num

