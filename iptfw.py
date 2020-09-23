#!/usr/bin/env python3
import iptc, socket, sys, json

def v4_lookup(host):
    try:
        ret = str(socket.getaddrinfo(host, None, socket.AF_INET)[0][4][0])
    except socket.gaierror:
        print('DNS Resolution Failed for {}'.format(host), file=sys.stderr)
        sys.exit(1)
    return ret


def loadConf( fn:str = ''):
    fh = open( fn, 'r')
    if fh:
        return json.loads( fh.read() )
    else:
        print('Failed to load config file {}.  Bailing...'.format(fn) )
        sys.exit(1)
    return None


def mkCFDDNSRule(hostnm: str = '', proto: str = '', portNum: str = '' ):
    rule = iptc.Rule()
    rule.protocol = proto
    rule.src = v4_lookup(hostnm)

    portmatch = iptc.Match(rule, proto)
    portmatch.dport = portNum

    connt = iptc.Match(rule, 'conntrack')
    connt.ctstate = 'NEW'

    commentm = iptc.Match(rule, 'comment')
    commentm.comment = '{}_{}_{}'.format( hostnm, proto, portNum )

    rule.add_match(portmatch)
    rule.add_match(connt)
    rule.add_match(commentm)

    tar = rule.create_target('ACCEPT')
    rule.target = tar
    return rule

def getRuleByComment( ch: iptc.Chain, cm: str = ''):
    for x in range(0, len(ch.rules) ):
        if not ch.rules[x].matches:
            return (None, -1)
        for i in range(0, len(ch.rules[x].matches) ):
            if not ch.rules[x].matches[i].name == 'comment':
                next
            elif ch.rules[x].matches[i].comment == cm:
                return (ch.rules[x], x)
            else:
                next
    return (None, -1)


if __name__ == '__main__':
    
    try:
        iptc.easy.add_chain('filter','CFDDNS_RULES')
    except:
        pass

    cfddns_chain = iptc.Chain(iptc.Table(iptc.Table.FILTER), "CFDDNS_RULES")

    # "fuck me gently with a chainsaw"
    config = loadConf(sys.argv[1])
    for k in config.keys():
        for proto in config[k].keys():
            for i in range(0, len(config[k][proto]) ):

                searchcomment = '{}_{}_{}'.format( k, proto, config[k][proto][i] )
                searchrule, ruleidx = getRuleByComment( cfddns_chain, searchcomment )

                if not searchrule:
                    #rule doesn't exist so make it
                    print('Rule not found.  Creating rule for {}:{}/{}...'.format( v4_lookup( k ), config[k][proto][i], proto ) )
                    newrule = mkCFDDNSRule(k, proto, config[k][proto][i])
                    cfddns_chain.append_rule( newrule )
                    next
                elif searchrule and (ruleidx >= 0):
                    # rule exists so check it
                    print('Rule found.  Checking for update...')
                    ruleip = searchrule.src.split('/')[0]
                    curip = v4_lookup( k )
                    if ruleip != curip:
                        # rule is out of date so update it

                        # ip:port/protocol eg. 10.1.1.1:80/tcp
                        print('Resolution change {}:{}/{} -> {}:{}/{}.  Updating...'.format(  ruleip, config[k][proto][i], proto, curip, config[k][proto][i], proto ) )

                        newrule = mkCFDDNSRule(k, proto, config[k][proto][i] )
                        cfddns_chain.delete_rule( searchrule )
                        cfddns_chain.insert_rule( newrule, ruleidx )
                        next
                    elif ruleip == curip:
                        print('Rule is current.  Skipping...')
                        next

                    #catchall below here
                    else:
                        print('foobar.', file=sys.stderr)
                        sys.exit(1)
                else:
                    print('foobar.', file=sys.stderr)
                    sys.exit(1)

    iptc.Table(iptc.Table.FILTER).commit()
    print('Done.')

    sys.exit(0)



    

