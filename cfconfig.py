#!/usr/bin/env python3
import json
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))

def confLoad(conf_file):
    try:
        fh = open(conf_file, "r")
    except:
        print("Unable to open configuration file: {}".format( conf_file ) )
        return None
    return json.loads(fh.read())

def confGetAPIToken(confstruct):
    return environ.get('CFDDNS_API_TOKEN')

def confGetZoneID(confstruct):
    return environ.get('CFDDNS_ZONEID')

def confGetHost( confstruct):
    return confstruct['ddns_host']

def confGetTTL( confstruct):
    return confstruct['ddns_ttl']

def confGetLogPath( confstruct ):
    return confstruct['logfile']

def confGetIPServers( confstruct ):
    return confstruct['GetIPServerList']

def confGetInterval( confstruct ):
    return confstruct['interval']

def confGetInterface( confstruct ):
    return confstruct['interface']

if __name__ == '__main__':
    import sys
    print( 'performing config test on {}...'.format( sys.argv[1] ) )

    confStruct = confLoad( sys.argv[1] )


    print( '[+] Token: {}\n[+] ZoneID: {}\n[+] DDNS Host: {}...\n[+] Log Path: {}...\n[+] Interval: {}...\n[+] interface: {}...'\
            .format( confGetAPIToken( confStruct ),\
                    confGetZoneID( confStruct ),\
                    confGetHost( confStruct),\
                    confGetLogPath( confStruct ),\
                    confGetInterval( confStruct ),\
                    confGetInterface( confStruct ) ) )

    for i in range(0, len( confGetIPServers( confStruct ) ) ):
        print( '[+] IP Server #{}: {}...'.format( i, confGetIPServers( confStruct)[i] ) )

    print('\ndone.')
    sys.exit(0)
