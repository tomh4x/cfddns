import requests, json, sys
import logging.handlers
from syslog import syslog, LOG_INFO

class cfdns:
    def __init__(self, zoneID: str ='', apiToken: str='' ):
        self.zoneID = zoneID
        self.apiToken = apiToken
        self.authHdr = { 'Authorization': '', 'Content-Type': 'application/json' }

        # internal use only
        self.baseURL = 'https://api.cloudflare.com/client/v4/zones/'
        if apiToken:
            self.authHdr = { 'Authorization': 'Bearer {}'.format( apiToken ), 'Content-Type': 'application/json' }

        syslog( LOG_INFO, 'cfdns instantiated successfully.')
        return

    def set_apiToken( self, APIToken ):
        self.apiToken = APIToken
        self.authHdr = { 'Authorization': 'Bearer {}'.format(APIToken), 'Content-Type': 'application/json' }
        syslog( LOG_INFO, 'API Token updated!' )
        return

    def set_zoneID( self, zid ):
        self.zoneID = zid
        syslog( LOG_INFO, 'Zone ID updated!' )
        return

    # Make sure keys from a given dict/query are all valid against master set
    # params: dictionaries like: { 'type':'A', 'content', 'x.x.x.x', 'name': 'somehost.example.com', 'ttl', 120 }
    # return: boolean
    def ValidateQueryKeys( self, query ):
        masterKeys = set(sorted([ 'name', 'ttl','type','content', 'proxied']))
        q = set(sorted(query))
        return q.issubset( masterKeys)

    # Validate credentials against API Endpoint
    def chk_creds(self):
        if self.zoneID and self.apiToken:
            try:
                #print( 'Auth Header: {}'.format( self.authHdr) )
                credchk = requests.get('https://api.cloudflare.com/client/v4/user/tokens/verify', headers = self.authHdr )
            except requests.exceptions.RequestException as e:
                print(e, file=sys.stderr)
                return False

            if credchk.status_code == 200  and credchk.json()['result']['status'] == 'active':
                #syslog( LOG_INFO, 'chk_creds(): success.')
                return True

            #if credchk and not credchk.json()['result']['status'] == 'active':
            else:
                syslog( LOG_INFO, 'chk_creds(): failed!')
                #pdb.set_trace()
                if credchk.status_code != 200:
                    syslog( LOG_INFO, 'Server Error Status Code: {}\n'.format( credchk.status_code ) )
                    print( credchk.json(), file=sys.stderr )

        return False

    # argument is a dictionary
    # keys:  type, content, name ttl
    # eg. { 'type':'A', 'content', 'x.x.x.x', 'name': 'somehost.example.com', 'ttl', 120 }
    # returns list of matching records.  eg return all A  records: {'type':'A' }
    def list_record(self, query ):
        if not self.chk_creds():
            return False

        # make sure parameter is a dict
        if type(query).__name__ != 'dict':
            return False

        # make sure no weird keys in the parameter by comparing 2 sets with isSubSet()
        #pdb.set_trace()
        if not self.ValidateQueryKeys( query ):
            syslog( LOG_INFO, 'list_record(): invalid key in query!')
            return False

        if len(query) == 0:
            return False

        payloadURL = self.baseURL + self.zoneID + '/dns_records?'

        try:
            #syslog( LOG_INFO, 'list_record(): {}'.format( query ) )
            ret = requests.get( payloadURL, params=query, headers=self.authHdr ) 
        except requests.exceptions.RequestException as e:
            print(e, file=sys.stderr)
            return False
        #syslog( LOG_INFO, 'list_record(): success.')
        return ret

    # argument is a dictionary
    # keys [REQUIRED]: type, name, content, ttl, proxied? 
    # eg. { 'type': 'A', 'name':'newhost.example.com', 'content': 'x.x.x.x', 'ttl': 7200, 'proxied': False }
    def add_record(self, newrec ):
        if not self.chk_creds():
            return False

        # make sure all dictionary keys were provided in param
        if sorted(newrec) != ['content', 'name', 'proxied', 'ttl', 'type']:
            return False

        try:
            #syslog( LOG_INFO, 'add_record(): {}'.format( newrec ) )
            ret = requests.post( self.baseURL + self.zoneID + '/dns_records', headers=self.authHdr, data=json.dumps(newrec) )
        except requests.exceptions.RequestException as e:
            print(e, file=sys.stderr)
            return False

        syslog( LOG_INFO, 'add_record(): success.')
        return ret


    # argument is a dictionary
    # keys:  type, content, name ttl
    # eg. { 'type':'A', 'content', 'x.x.x.x', 'name': 'somehost.example.com', 'ttl', 120 }
    # return a specific individual record ID when query matches a single result
    def get_recordID(self, query ):

        ret = self.list_record( query)
        if ret:
            if len(ret.json()['result']) == 1:
                syslog( LOG_INFO, 'get_recordID(): {}'.format(ret.json()['result'][0]['id']) )
                return ret.json()['result'][0]['id']
        else:
            syslog( LOG_INFO, 'get_recordID(): failed.')

        return None

    # query param is a dictionary
    # keys REQUIRED: type, name, content
    # keys OPTIONAL: ttl, proxied
    # eg. { 'type': 'A', 'name':'newhost.example.com', 'content': 'x.x.x.x', 'ttl': 7200, 'proxied': False }
    #
    # dnsid is a string returned by get_recordID
    def update_record( self, query, dnsid=None):

        # if we don't have at lease these keys set then bail out
        qkeys = query.keys()
        if 'type' not in qkeys or 'name' not in qkeys or 'content' not in qkeys:
            return False
        
        # Attempt to locate dnsid on the fly because no dnsid parameter provided
        # NOTE: this lookup will only work if searching by record type and name yields 1 single result in the set
        if not dnsid:
            dnsid = self.get_recordID( { 'type': query['type'], 'name': query['name'] } )

        # lookup failed
        if not dnsid:
            return False
        try:
            syslog( LOG_INFO, 'update_record(): {}'.format( query ) )
            ret = requests.put( self.baseURL + self.zoneID + '/dns_records/' + dnsid, headers=self.authHdr, data=json.dumps(query) )
        except requests.exceptions.RequestException as e:
            print(e, file=sys.stderr)
            return False
        syslog( LOG_INFO, 'update_record(): success.')
        return ret

    def del_record(self, dnsid ):
        if not self.chk_creds():
            return False
        syslog( LOG_INFO, 'del_record(): {}'.format( dnsid ) )
        try:
            retreq = requests.delete( self.baseURL + self.zoneID + '/dns_records/' + dnsid, headers=self.authHdr)
        except requests.exceptions.RequestException as e:
            print(e, file=sys.stderr)
            return False

        syslog( LOG_INFO, 'del_record(): success.')
        return retreq



