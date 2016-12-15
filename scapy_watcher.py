"""scapy_watcher.py: watches network packets, calculates speed and totals per-port."""

__author__ = "Alex 'Chozabu' P-B"
__copyright__ = "Copyright 2016, Chozabu"


import netifaces

from threading import Thread
from scapy.all import *

last_time = time.time()

portcounts = {}

def calc_speeds():
    global last_time
    # update speed counters
    new_time = time.time()
    if new_time > last_time+1:
        last_time+=1
        for k in portcounts.keys():
            v = portcounts[k]
            diff = v['total'] - v['last']
            v['last'] = v['total']
            v['speed_raw'] = diff
            v['speed'] = v['speed']*.9 + diff *.1

        #find and print port using most bandwidth each second
        topport = -1
        topport_speed = -1
        for k in portcounts.keys():
            v = portcounts[k]
            if v['speed'] > topport_speed:
                topport = k
                topport_speed = v['speed']
        if topport != -1:
            print("heaviest port:", topport, portcounts[topport])

def pkt_callback(pkt):
    #pkt.show() # debug statement
    #print(pkt.fields)
    #print(pkt.fields_desc)
    #print("dport", pkt['TCP'].dport, "sport", pkt['TCP'].sport)
    #print()

    datalen = len(pkt)
    sport = pkt['TCP'].sport

    if sport not in portcounts:
        portcounts[sport] = {"total": 0, "last": 0, "speed_raw": 0, "speed": 0, "port": sport}
    portcounts[sport]['total'] += datalen

    calc_speeds()

def run():
    ifaces = [iface for iface in netifaces.interfaces()
              if netifaces.AF_INET in netifaces.ifaddresses(iface)]
    sniff(iface=ifaces, prn=pkt_callback, filter="tcp", store=0)


def launch_watcher():
    run()

def start_background_thread():
    try:
        t = Thread(
            daemon=True,
            target=launch_watcher,
            kwargs={})
    except:
        t = Thread(
            target=launch_watcher,
            kwargs={})
        t.daemon = True
    t.start()

if __name__ == '__main__':
    run()
