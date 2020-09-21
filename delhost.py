#!/usr/bin/env python3
import cloudflare, sys
from cfconfig import *
from getAddr import getAddrFromPub
from random import randint

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: {} [/path/to/confFile]'.format( sys.argv[0]) )
        sys.exit(1)

    config = confLoad( sys.argv[1] )
    ddom = cloudflare.cfdns()

    # set creds
    ddom.set_apiToken( confGetAPIToken(config) )
    ddom.set_zoneID( confGetZoneID(config) )

    hostname = confGetHost(config)
    recID = ddom.get_recordID( {'type':'A', \
                                'name': confGetHost(config), \
                                'content': getAddrFromPub( confGetIPServers(config)[randint(0,3)] ), \
                                'ttl': 120 } \
                                )
    if recID:
        print('Got record ID: {}\nSending delete request...'.format(recID) )
        resp = ddom.del_record( recID )
        if not resp:
            print('Failed!!', file=sys.stderr)
        else:
            print('Validating record deletion...')
            vrecID = ddom.get_recordID( {'type':'A', \
                                'name': confGetHost(config), \
                                'content': getAddrFromPub( confGetIPServers(config)[randint(0,3)] ), \
                                'ttl': 120 } \
                                )
            if not vrecID:
                print('Record successfully deleted.')
    else:
        print('No A record for {} to delete.'.format( confGetHost(config) ) )
sys.exit(0)

    