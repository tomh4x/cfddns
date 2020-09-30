#!/usr/bin/env python3

import cloudflare, os, sys, json
from syslog import syslog, LOG_INFO
from cfconfig import *
from getAddr import getAddrFromPub
from time import sleep
from signal import signal, SIGINT, SIGTERM

def sig_handler(sig, frame):
    syslog( LOG_INFO, 'Signal {} Received: Exit.'.format(sig) )
    sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: {} /path/to/configFile'.format(sys.argv[0]) )
        sys.exit(0)
    
    # catch ctrl-c
    signal(SIGINT, sig_handler)
    signal(SIGTERM, sig_handler)

    config = confLoad( sys.argv[1] )
    if not config:
        print('Failed to load config file.  Bailing out', file=sys.stderr)
        sys.exit(-1)

    syslog(LOG_INFO, 'logging initialized')
    # instantiate cloudflare dns class and load config
    ddom = cloudflare.cfdns()

    # set creds
    ddom.set_apiToken( confGetAPIToken(config) )
    ddom.set_zoneID( confGetZoneID(config) )

    # BEGIN INFINITE EVENT LOOP
    # TODO: handle ctrl+c signal interrupt as well as SIGKILL and SIGTERM
    while( True ):
        new_rec = {'type':'A', \
                    'name':confGetHost(config), \
                    'content': getAddrFromPub( confGetIPServers(config) ), \
                    'ttl': confGetTTL(config), \
                    'proxied': False }

        current_rec = {'type':'A', 'name': confGetHost(config) }
        syslog( LOG_INFO, 'checking for existing host...')

        # check for A record of the host assigned from config and current IP:
        recID = ddom.get_recordID( {'type':'A', \
                                    'name': confGetHost(config), \
                                    'content': getAddrFromPub( confGetIPServers(config) ), \
                                    'ttl': confGetTTL(config) } )

        if recID:
            # everything is all good.  re-iterate event loop
            syslog( LOG_INFO,  'A record is set.  Waiting {} seconds...'.format( confGetInterval(config) ))
            sleep( confGetInterval(config) )
            next
            
        else:
            syslog( LOG_INFO, 'Existing host was missing or incorrect...')
            # something isn't good
            # check if host exists regardless of IP
            ret = ddom.list_record( current_rec )
            if not ret:
                syslog( LOG_INFO, 'no http response!')

            # if we got a status 200 response with at least 1 result, it exists!
            if ret and ret.status_code==200 and len(ret.json()['result']) > 0:
                syslog( LOG_INFO, 'Outdated IP.  Updating...')
                # we probably just need to update the record
                upret = ddom.update_record( new_rec )
                if upret and upret.status_code == 200:
                    next
                else:
                    syslog( LOG_INFO, 'Failed to update record.  Something is wrong.  Bailing out!')
                    sys.exit(-1)
            
            # bad API key.  chk_creds() should catch this
            elif ret and ret.status_code == 401:
                syslog( LOG_INFO, 'Authentication failure.  Bailing out!')
                sys.exit(-1)

            # something else that makes no sense happened
            elif ret and ret.status_code != 200:
                syslog( LOG_INFO, 'HTTP Response code: {}: try again next time.'.format( ret.status_code) )
                sys.exit(-1)

            # everything is fine except the record doesn't exist so make it.
            elif ret and ret.status_code == 200 and len(ret.json()['result']) == 0:
                syslog( LOG_INFO, 'Record does not exist!  Creating...')
                ret = ddom.add_record( new_rec)
                if ret and ret.status_code == 200:
                    syslog( LOG_INFO, 'Record creation completed!')
                    # record should detect on next iteration and wait nicely
                    next

            # catchall
            else:
                # probably no http response
                syslog( LOG_INFO, 'Something went very wrong!  No http response received!')
                syslog( LOG_INFO, 'Bailing out!')
                sys.exit(-1)
    # END EVENT LOOP
    sys.exit(0)
    
    

