"""Foobar.py: Description of what foobar does."""

__author__ = "Alex 'Chozabu' P-B"
__copyright__ = "Copyright 2016, IAgree"

import subprocess

interface = "wlp3s0"
LINKCEIL="1gbit"
ipt="/sbin/iptables"
LOCALNET="192.168.0.0/16"

traffic_classes = {
    11: {
        "mark":33,
        "limit":50
    },
    12: {
        "mark":44,
        "limit":90
    }
}

port_limits = {
    80: {
        "up":33,
        "down":33
    },
    48180: {
        "up":33,
        "down":33
    },
    49144: {
        "up":33,
        "down":33
    },
    57084: {
        "up":33,
        "down":33
    },
    5001: {
        "up":33,
        "down":44
    }
}



reset_net = '''
# Copyright (c) 2013 The Bitcoin Core developers & Chozabu
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#limit of the network interface in question
LINKCEIL="1gbit"

#defines the address space for which you wish to disable rate limiting


#delete existing rules
echo "resetting tc"
tc qdisc del dev {interface} root

#delete any existing rules
echo "resetting iptables"
ipt="{ipt}"

$ipt -P INPUT ACCEPT
$ipt -P FORWARD ACCEPT
$ipt -P OUTPUT ACCEPT
$ipt -F INPUT -t mangle
$ipt -F OUTPUT -t mangle
$ipt -F FORWARD -t mangle
$ipt -t mangle -F
$ipt -t mangle -X


echo "setting tc"

#add root class
tc qdisc add dev {interface} root handle 1: htb default 10

#add parent class
tc class add dev {interface} parent 1: classid 1:1 htb rate {LINKCEIL} ceil {LINKCEIL}

#add our two classes. one unlimited, another limited
tc class add dev {interface} parent 1:1 classid 1:10 htb rate {LINKCEIL} ceil {LINKCEIL} prio 0

#add handles to our classes so packets marked with <x> go into the class with "... handle <x> fw ..."
tc filter add dev {interface} parent 1: protocol ip prio 1 handle 1 fw classid 1:10
'''.format(interface=interface, LINKCEIL=LINKCEIL, ipt=ipt)


tclass =  "tc class add dev {interface} parent 1:1 classid 1:{tcid} htb rate {LIMIT}kbit ceil {LIMIT}kbit prio 1"
tfilter = "tc filter add dev {interface} parent 1: protocol ip prio 2 handle {mark} fw classid 1:{tcid}"


markout = '''
iptables -t mangle -A OUTPUT -p tcp -m tcp --dport {PORT} ! -d {LOCALNET} -j MARK --set-mark {mark}
iptables -t mangle -A OUTPUT -p tcp -m tcp --sport {PORT} ! -d {LOCALNET} -j MARK --set-mark {mark}
'''

markin = '''
iptables -t mangle -A INPUT -p tcp -m tcp --dport {PORT} ! -d {LOCALNET} -j MARK --set-mark {mark}
iptables -t mangle -A INPUT -p tcp -m tcp --sport {PORT} ! -d {LOCALNET} -j MARK --set-mark {mark}
'''

def run(commands):
    process = subprocess.Popen('/bin/bash', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    return process.communicate(commands)

def reset_all():
    out, err = run(reset_net)
    print "done\n", out

def set_limits():
    for k, v in traffic_classes.iteritems():
        ccmd = tclass.format(interface=interface, tcid=k, LIMIT=v['limit'])
        out, err = run(ccmd)
        print "set class for",k,v, out, ccmd
        tcmd = tfilter.format(interface=interface, tcid=k, mark=v['mark'])
        out, err = run(tcmd)
        print "set filter for",k,v, out, tcmd

    for k, v in port_limits.iteritems():
        if 'up' in v:
            ocmd = markout.format(LOCALNET=LOCALNET, PORT=k, mark=v['up'])
            out, err = run(ocmd)
            print "set uplimit for",k,v, out, ocmd
        if 'down' in v:
            icmd = markin.format(LOCALNET=LOCALNET, PORT=k, mark=v['down'])
            out, err = run(icmd)
            print "set downlimit for",k,v, out, icmd

def set_from_ports_list(port_dict):
    global traffic_classes, port_limits
    traffic_classes = {}
    port_limits = {}

    class_lookup = {}

    currentClass = 11
    for d in port_dict:
        ul = d['up_limit']
        dl = d['down_limit']
        prt = d['port']
        new_info = {}

        if ul not in class_lookup:
            traffic_classes[currentClass] = {
                'mark': currentClass,
                'limit': ul
            }
            class_lookup[ul] = currentClass
            new_info['up'] = currentClass
            currentClass += 1
        else:
            new_info['up'] = class_lookup[ul]

        if dl not in class_lookup:
            traffic_classes[currentClass] = {
                'mark': currentClass,
                'limit': dl
            }
            class_lookup[dl] = currentClass
            new_info['down'] = currentClass
            currentClass += 1
        else:
            new_info['down'] = class_lookup[dl]

        port_limits[prt] = new_info

    print "PORT LIMITS", port_limits
    print "TClasses", traffic_classes
    reset_all()
    set_limits()

if __name__ == '__main__':
    reset_all()
    set_limits()
