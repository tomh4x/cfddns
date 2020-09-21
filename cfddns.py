#!/usr/bin/env python3

import cloudflare, logging, os, sys, json
from cfconfig import *
from getAddr import getAddrFromPub
from time import sleep
from random import randint


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: {} /path/to/configFile'.format(sys.argv[0]) )
        sys.exit(0)
    
    config = confLoad( sys.argv[1] )
    if not config:
        print('Failed to load config file.  Bailing out')
        sys.exit(-1)

    logging.basicConfig(filename=confGetLogPath(config), format='[%(asctime)s] %(message)s', datefmt='%b %d %Y %H:%M:%S', level=logging.INFO)
    logging.info('logging instantiated')
    #instantiate cloudflare dns class and load config
    ddom = cloudflare.cfdns()

    # set creds
    ddom.set_apiToken( confGetAPIToken(config) )
    ddom.set_zoneID( confGetZoneID(config) )

    # BEGIN INFINITE EVENT LOOP
    # TODO: handle ctrl+c signal interrupt as well as SIGKILL and SIGTERM
    while( True ):
        new_rec = {'type':'A', \
                    'name':confGetHost(config), \
                    'content': getAddrFromPub( confGetIPServers(config)[randint(0,3)] ), \
                    'ttl': 120, \
                    'proxied': False }

        current_rec = {'type':'A', 'name': confGetHost(config) }
        logging.info('checking for existing host...')

        # check for A record of the host assigned from config and current IP:
        recID = ddom.get_recordID( {'type':'A', \
                                    'name': confGetHost(config), \
                                    'content': getAddrFromPub( confGetIPServers(config)[randint(0,3)] ), \
                                    'ttl': 120 } )

        if recID:
            # everything is all good.  re-iterate event loop
            logging.info( 'A record is set.  Waiting {} seconds...'.format( confGetInterval(config) ))
            sleep( confGetInterval(config) )
            next
            
        else:
            logging.info('Existing host was missing or incorrect...')
            # something isn't good
            # check if host exists regardless of IP
            ret = ddom.list_record( current_rec )

            # if we got a status 200 response with at least 1 result, it exists!
            if ret and ret.status_code==200 and len(ret.json()['result']) > 0:
                logging.info('Outdated IP.  Updating...')
                # we probably just need to update the record
                upret = ddom.update_record( new_rec )
                if upret and upret.status_code == 200:
                    next
                else:
                    logging.info('Failed to update record.  Something is wrong.  Bailing out!')
                    sys.exit(-1)
            
            # bad API key.  chk_creds() should catch this
            elif ret and ret.status_code == 401:
                logging.info('Authentication failure.  Bailing out!')
                sys.exit(-1)

            # something else that makes no sense happened
            elif ret and ret.status_code != 200:
                logging.info('HTTP Response code: {}: try again next time.'.format( ret.status_code) )
                sys.exit(-1)

            # everything is fine except the record doesn't exist so make it.
            elif ret and ret.status_code == 200 and len(ret.json()['result']) == 0:
                logging.info('Record does not exist!  Creating...')
                ret = ddom.add_record( new_rec)
                if ret and ret.status_code == 200:
                    logging.info('Record creation completed!')
                    # record should detect on next iteration and wait nicely
                    next

            # catchall
            else:
                # probably no http response
                logging.info('Something went very wrong!  No http response received!')
                logging.info('Bailing out!')
                sys.exit(-1)
    # END EVENT LOOP
    sys.exit(0)
    
    

