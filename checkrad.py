#!/usr/bin/python

import sys
import re
import datetime as dt
from subprocess import Popen, PIPE
from time import time

def getSNMPLines():
    for oid in oids:
        params = ['snmpwalk', '-t1', '-r1', '-v1', '-cpublic', nasip, oid]
        snmp = Popen(params, stdout=PIPE, stderr=None)
        out = snmp.communicate()[0]

        for snmpline in out.splitlines():
            yield snmpline

def checkLine(lin):
    for rexp in regexps:
        if rexp.search(lin):
            return True

    return False


if len(sys.argv) < 6:
    print 'Usage: checkrad nas_type nas_ip nas_port login session_id'
    sys.exit(0)

nastype = sys.argv[1]
nasip = sys.argv[2]
username = sys.argv[4]

oids = []
regexps = []

if ('snmp' in nastype) or ('pppoe' in nastype):
    oids.append('ifdescr')
    regexps.append(r'<pppoe-(%s)>' % username)

if 'hotspot' in nastype:
    oids.append('enterprises.14988.1.1.5.1.1.3')
    regexps.append(r'STRING: \"(%s)\"' % username)

regexps = [re.compile(regexp) for regexp in regexps]

start = time()
exitcode = 0

for line in getSNMPLines():
    if checkLine(line):
        exitcode = 1
        break

end = time()-start

if exitcode == 0:
    retmsg = 'Login OK'  
else:
    retmsg ='Double detected'
    
date = dt.datetime.now().strftime('%d/%m %H:%M:%S')
output = "%s - Nas: %s Tipo: %s Login: %s - %s (%.3f)" % (
    date, nasip, nastype, username, retmsg, end
)
log = open('/var/log/radius/checkrad.log','a')
print >>log, output
#~ print output
sys.exit(exitcode)
