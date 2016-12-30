#!/usr/bin/env bash

set -o xtrace

IF="wlp3s0"
LIMIT="10000kbit"
BURST="100kbit"
PORT="80"

echo "resetting tc"
tc qdisc del dev ${IF} root
tc qdisc del dev ${IF} ingress

echo "setting tc"
tc qdisc add dev ${IF} handle ffff: ingress
#tc filter add dev ${IF} parent ffff: protocol ip prio 1 \
#   u32 match ip dport ${PORT} 0xffff police rate ${LIMIT} \
#   burst $BURST flowid :1
#tc filter add dev ${IF} parent ffff: protocol ip prio 1 \
#   u32 match ip sport ${PORT} 0xffff police rate ${LIMIT} \
#   burst $BURST flowid :1

tc filter add dev ${IF} parent ffff: \
   protocol ip prio 1 \
   u32 match ip dport ${PORT} 0xffff \
   police rate ${LIMIT} burst $BURST drop \
   flowid :1
tc filter add dev ${IF} parent ffff: \
   protocol ip prio 1 \
   u32 match ip sport ${PORT} 0xffff \
   police rate ${LIMIT} burst $BURST drop \
   flowid :1