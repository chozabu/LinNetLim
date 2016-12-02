#!/usr/bin/env python
""" Example: Simple Packet Printer """
import os
import argparse

# Local imports
from chains.utils import signal_utils
from chains.sources import packet_streamer
from chains.links import packet_meta, reverse_dns, transport_meta
from chains.sinks import packet_printer, packet_summary

import time

from chains.sinks import sink
from chains.utils import net_utils

portcounts = {}


class PacketPrinter(sink.Sink):
    """Print packet information"""

    def __init__(self, color_output=True):
        """Initialize PacketPrinter Class"""

        # Call super class init
        super(PacketPrinter, self).__init__()

        # Should we add color on the output
        self._color = color_output

    def pull(self):
        """Print out information about each packet from the input_stream"""

        # For each packet in the pcap process the contents
        for item in self.input_stream:

            # Print out the timestamp in UTC
            print 'Timestamp: %s' % item['timestamp']

            # Unpack the Ethernet frame (mac src/dst, ethertype)
            print 'Ethernet Frame: %s --> %s  (type: %d)' % \
                  (net_utils.mac_to_str(item['eth']['src']), net_utils.mac_to_str(item['eth']['dst']), item['eth']['type'])

            # Print out the Packet info
            packet_type = item['packet']['type']
            print 'Packet: %s' % packet_type,
            packet = item['packet']
            if packet_type in ['IP', 'IP6']:
                print '%s --> %s (len:%d ttl:%d)' % (net_utils.inet_to_str(packet['src']), net_utils.inet_to_str(packet['dst']),
                                                     packet['len'], packet['ttl']),
                if packet_type == 'IP':
                    print '-- Frag(df:%d mf:%d offset:%d)' % (packet['df'], packet['mf'], packet['offset'])
                else:
                    print
            else:
                print str(packet)

            # Print out transport and application layers
            if item['transport']:
                transport_info = item['transport']
                print 'Transport: %s ' % transport_info['type'],
                for key, value in transport_info.iteritems():
                    if key != 'data':
                        print key+':'+repr(value),

                # Give summary info about data
                data = transport_info['data']
                print '\nData: %d bytes' % len(data),
                if data:
                    print '(%s...)' % repr(data)[:30]
                else:
                    print

            # Application data
            if item['application']:
                print 'Application: %s' % item['application']['type'],
                print str(item['application'])

            # Is there domain info?
            if 'src_domain' in packet:
                print 'Domains: %s --> %s' % (packet['src_domain'], packet['dst_domain'])

            # Tags
            if 'tags' in item:
                print list(item['tags'])
            print
            print(item)
            print("\n")


class PacketCounter(sink.Sink):
    """Print packet information"""

    def __init__(self, color_output=True):
        """Initialize PacketPrinter Class"""

        # Call super class init
        super(PacketCounter, self).__init__()

        # Should we add color on the output
        self._color = color_output
        self.last_time = time.time()

    def pull(self):
        """Print out information about each packet from the input_stream"""

        # For each packet in the pcap process the contents
        for item in self.input_stream:

            # Unpack the Ethernet frame (mac src/dst, ethertype)
            #print 'Ethernet Frame: %s --> %s  (type: %d)' % \
            #      (net_utils.mac_to_str(item['eth']['src']), net_utils.mac_to_str(item['eth']['dst']), item['eth']['type'])

            # gather data usage per port
            if item['transport']:
                transport_info = item['transport']
                data = transport_info['data']
                datalen = len(data)

                if 'sport' in transport_info and datalen:
                    sport = transport_info['sport']
                    if sport not in portcounts:
                        portcounts[sport] = {"total": 0,"last": 0,"speed_raw": 0,"speed": 0, "port":sport}
                    portcounts[sport]['total'] += datalen
            #print(portcounts)

            # update speed counters
            new_time = time.time()
            if new_time > self.last_time+1:
                self.last_time+=1
                for k,v in portcounts.iteritems():
                    diff = v['total'] - v['last']
                    v['last'] = v['total']
                    v['speed_raw'] = diff
                    v['speed'] = v['speed']*.9 + diff *.1

                #find and print port using most bandwidth each second
                topport = -1
                topport_speed = -1
                for k,v in portcounts.iteritems():
                    if v['speed'] > topport_speed:
                        topport = k
                        topport_speed = v['speed']
                if topport != -1:
                    print(topport, portcounts[topport])

def run(iface_name=None, bpf=None, summary=None, max_packets=100):
    """Run the Simple Packet Printer Example"""

    # Create the classes
    streamer = packet_streamer.PacketStreamer(iface_name=iface_name, bpf=bpf, max_packets=max_packets)
    meta = packet_meta.PacketMeta()
    rdns = reverse_dns.ReverseDNS()
    tmeta = transport_meta.TransportMeta()
    printer = PacketCounter()

    # Set up the chain
    meta.link(streamer)
    rdns.link(meta)
    tmeta.link(rdns)
    printer.link(tmeta)

    # Pull the chain
    printer.pull()

def test():
    """Test the Simple Packet Printer Example"""
    from chains.utils import file_utils

    # For the test we grab a file, but if you don't specify a
    # it will grab from the first active interface
    data_path = file_utils.relative_dir(__file__, '../data/http.pcap')
    run(iface_name = data_path)

def my_exit():
    """Exit on Signal"""
    print 'Goodbye...'

if __name__ == '__main__':

    # Collect args from the command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-bpf', type=str, help='BPF Filter for PacketStream Class')
    parser.add_argument('-s','--summary', action="store_true", help='Summary instead of full packet print')
    parser.add_argument('-m','--max-packets', type=int, default=10, help='How many packets to process (0 for infinity)')
    parser.add_argument('-p','--pcap', type=str, help='Specify a pcap file instead of reading from live network interface')
    args, commands = parser.parse_known_args()
    if commands:
        print 'Unrecognized args: %s' % commands
    try:
        # Pcap file may have a tilde in it
        if args.pcap:
            args.pcap = os.path.expanduser(args.pcap)

        with signal_utils.signal_catcher(my_exit):
            run(iface_name=args.pcap, bpf=args.bpf, summary=args.summary, max_packets=args.max_packets)
    except KeyboardInterrupt:
        print 'Goodbye...'
