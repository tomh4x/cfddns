#!/usr/bin/env python3

import socket, fcntl, struct
from requests import get
from re import match

def getAddrFromIface(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa( fcntl.ioctl(s.fileno(),0x8915,struct.pack('256s', bytes(ifname[:15].encode('utf-8'))) )[20:24] )

def getAddrFromPub(svcurl):
    try:
        val = get(svcurl)
    except requests.exceptions.RequestException as e:
        print(e, file=sys.stderr)
        return False
    return match('^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', val.text).group()

if __name__ == '__main__':
    from cfconfig import *
    import sys
    if len(sys.argv) != 2:
        print('Import this as a module or run with:\n\nUsage: {} /path/to/config'.format( sys.argv[0]) )
        sys.exit(0)
    conf = confLoad( sys.argv[1])
    ipservers = confGetIPServers(conf)
    for addr in ipservers:
        print('[{}]: {}'.format( addr, getAddrFromPub(addr)) )
    #print('iface [ens3]: {}'.format( getAddrFromIface('ens3') ) )


    sys.exit(0)
