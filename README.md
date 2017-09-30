# NetSim

A proof of concept for communication between a receiver and a transmitter over a simulated "noisy" channel.

### Features

The NetSim project attempts to demonstrates how TCP packets over a "noisy" channel behave between two users. The project shows how TCP packets can be received and sent over a communication channel and deal with added noise over the network. This noise is simulated by randomly dropping packets and instructing the receiver to resend those packets.

The Network Emulator implements the following features:
* Send-and-Wait: the transmitter sends and then waits for the receiver to respond back with ACKs before the transmitter sends again
* Retransmission: The transmitter will retry packets that have not had their ACK received by the transmitter until it has emptied its queue either after a specified time or if the EOT from the receiver is sent after it has finished sending ACKs
* Output: each piece of the emulator outputs to file and to screen for visibility
* Configuration: a configuration file is available to specify ports, hostnames, and percent packet loss
* All communications are done over a UDP socket


#### Usage

You must run all the components in a particular order to establish the connection between the receiver, transmitter and channel. 

```
python channel.py
python receiver.py
python transmitter.py <number_of_packets_to_send> <
```

#### The Transmitter

The transmitter sends packets to the [channel](channel.py) and keeps track of packets awaiting acknowledgement. In order to achieve 
this, the transmitter opens two sockets: one for transmitting to the channel and another for receiving from the channel. 
These are specified in the [configuration file](config.ini).

```
[transmitter]
host = localhost
port = 5000
```

The transmitter begins by taking in an input for the number of packets to send at a time and hold in its queue. This is  defined as the first command line argument. 

The transmitter’s main function is to maintain a continuous loop that keeps sending a set of packets at a time. The main loop has another function that has two functions:
* Create and send the packet to the channel, add packet sequence number to a list until you reach the window length
* Retrieve ACK packets from the channel and remove those sequence numbers from the list until they have all been ACK’d
When the above two functions have been satisfied, the transmitter does the same two functions again.


#### The Receiver

The receiver begins by connecting to the channel and listening for incoming packets on the receive port. When it receives packets, it accepts everything until an EOT is received. When an EOT is received, the Receiver begins sending ACKs back for every sequence number that it received. The Receiver always ACKs the sequence number it received and sends a packet back with an incremented sequence number. In other words, if the Receiver is ACKing a packet with sequence number 4, and it has 8 packets in total ready to be ACK’d, the sequence number of the ACK packet will be 9. This is done to ensure that there cannot be packets that come back from the Transmitter with overlapping sequence numbers. The Sequence numbering system will always increment (except for when retransmitting)

The Receiver does not take any inputs and simply accepts the window size that the transmitter sent as the authoritative window size. As with the Transmitter, the ports for bind and connect to and from the channel are specified in the [configuration file](config.ini).

```
[receiver]
host = localhost
port = 5003
```

The Receiver has two main functions, which are to collect the packets until an EOT is received, then send ACKs back to the channel for every packet received.

#### The Channel

The channel is complex in that I have designed it with 3 main pieces:
* The producer (transmitter socket)
* The consumer (receiver socket)
* A queue

The channel operates as a multithreaded process in which the producer and consumer are both separate threads. The main thread instantiates a queue using

```
from multiprocessing import Queue
q = Queue()
```

The queue is a shared resource in which both threads can interact with. Each thread either places a data object into the queue to be consumed, or consumes from the queue if there are objects to be consumed. This functionality is dependent on which process is currently allowed to send or receive (transmitter sending or receiving versus the receiver transmitting or receiving).

##### The Producer/Consumer
The producer operates by establishing a connection with the Transmitter for both sending and receiving data over the sockets. It determines whether or not it should be listening on the sockets for data from the Transmitter, or if it should be actively polling the queue for messages from the Consumer. This is done by inspecting the packets at a very basic level for the packet type. If an EOT is transmitted over the connection, it switches “modes” from “put” to “get”. Being in “get” mode tells the producer that it is now listening for messages on the queue to get and then send to the Transmitter. Being in “put” mode tells the producer that it is now listening for messages on the socket from the Transmitter and putting them in the queue.

Similarly, the Consumer operates the same way except in reverse. When the channel identifies an EOT packet, it applies a global variable that switches the direction that the two threaded processes operate. This helps establish the “send-and-wait” criteria.

##### Packet Loss Generation
Packet loss on the channel is generated by a specific config variable known as `noise_percent_loss` and is applied at both the producer and consumer but only once. Depending on what Mode the channel is operating in, it will be applied either at the “put” or “get” level of a particular thread. The packet loss is generated by applying a random number generator for each packet passing through the channel. If the random number generator meets the percentage threshold (0-1), the packet is dropped. This applies to data packets, ACK packets, and EOT packets. 

```
[channel]
bind = localhost
ingress_port = 5000
egress_port = 5001
noise_percent_loss = 0
```

### Prerequisites

* Python 2.7+

## Built With

* [Python](https://python.org) - The web framework used

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

We use [SemVer](http://semver.org/) for versioning. For the versions available, see the [tags on this repository](https://github.com/ghTravis/NetSim/tags).

* 1.0.0 - **Initial version** - Pushed to GitHub for public viewing

## Authors

* **Travis Ryder** - *Owner* - [TravisRyder.com](https://tavisryder.com)

See also the list of [contributors](https://github.com/ghTravis/NetSim/graphs/contributors) who participated in this project.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* BCIT BTech Program
