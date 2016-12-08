# Copyright (c) 2013 The Bitcoin Core developers & Chozabu
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#this altered version of tc.sh not used by LinNetLim - but kepts as a reference

#network interface on which to limit traffic
IF="wlp3s0"
#limit of the network interface in question
LINKCEIL="1gbit"
#limit outbound in/out on selected port to this rate
LIMIT="1000kbit"
BURST="15k"
PORT="80"
#defines the address space for which you wish to disable rate limiting
LOCALNET="192.168.0.0/16"



#delete existing rules
echo "resetting tc"
tc qdisc del dev ${IF} root
tc qdisc del dev ${IF} ingress

#delete any existing rules
echo "resetting iptables"
ipt="/sbin/iptables"
## Failsafe - die if /sbin/iptables not found 
[ ! -x "$ipt" ] && { echo "$0: \"${ipt}\" command not found."; exit 1; }
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
tc qdisc add dev ${IF} root handle 1: htb default 10
tc qdisc add dev ${IF} handle ffff: ingress
tc filter add dev ${IF} parent ffff: protocol ip prio 1 \
   u32 match ip dport ${PORT} 0xffff police rate ${LIMIT} \
   burst $BURST flowid :1
tc filter add dev ${IF} parent ffff: protocol ip prio 1 \
   u32 match ip sport ${PORT} 0xffff police rate ${LIMIT} \
   burst $BURST flowid :1

tc filter add dev wlp3s0 parent ffff: protocol ip prio 1 \
    u32 match ip dport 80 0xffff police rate 5kbit \
        burst $BURST flowid :1



#tc filter add dev ${IF} parent ffff: protocol ip prio 50 u32 match ip src \
#   0.0.0.0/0 police rate ${LIMIT} burst 20k drop flowid :1

#add parent class
tc class add dev ${IF} parent 1: classid 1:1 htb rate ${LINKCEIL} ceil ${LINKCEIL}

#add our two classes. one unlimited, another limited
tc class add dev ${IF} parent 1:1 classid 1:10 htb rate ${LINKCEIL} ceil ${LINKCEIL} prio 0



##loop this for each rule
#tc class add dev ${IF} parent 1:1 classid 1:11 htb rate ${LIMIT} ceil ${LIMIT} prio 1

#tc class add dev ${IF} parent 1:1 classid 1:13 htb rate ${LIMIT} burst 15k
tc class add dev ${IF} parent 1:1 classid 1:14 htb rate ${LIMIT} burst 15k

#add handles to our classes so packets marked with <x> go into the class with "... handle <x> fw ..."
#tc filter add dev ${IF} parent 1: protocol ip prio 1 handle 1 fw classid 1:10



##loop this for each rule
#tc filter add dev ${IF} parent 1: protocol ip prio 2 handle 6 fw classid 1:13
#tc filter add dev ${IF} parent 1: protocol ip prio 2 handle 7 fw classid 1:13
tc filter add dev ${IF} parent 1: protocol ip prio 2 handle 8 fw classid 1:14


##loop this for each rule
echo "setting iptables"
#limit outgoing traffic to and from port 8333. but not when dealing with a host on the local network
#	(defined by $LOCALNET)
#	--set-mark marks packages matching these criteria with the number "2"
#	these packages are filtered by the tc filter with "handle 2"
#	this filter sends the packages into the 1:11 class, and this class is limited to ${LIMIT}
iptables -t mangle -A OUTPUT -p tcp -m tcp --dport ${PORT} ! -d ${LOCALNET} -j MARK --set-mark 8
iptables -t mangle -A OUTPUT -p tcp -m tcp --sport ${PORT} ! -d ${LOCALNET} -j MARK --set-mark 8
#limit incoming traffic
#iptables -t mangle -A INPUT -p tcp -m tcp --dport ${PORT} -j MARK --set-mark 7
#iptables -t mangle -A INPUT -p tcp -m tcp --sport ${PORT} -j MARK --set-mark 7


