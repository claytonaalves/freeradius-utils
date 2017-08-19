#!/usr/bin/env python2
#coding: utf8
import sys
import argparse

sys.path.append('vendor')

import iplib
import MySQLdb

database_connection = None

class Pool:

    def __init__(self, pool_name, pool_address):
        self.name = pool_name
        self.address = '.'.join(pool_address.split('.')[0:3]) + '.0/24'

    def __repr__(self):
        return "Pool({0}, {1})".format(self.name, self.address)

    def __eq__(self, other):
        if isinstance(other, Pool):
            return ((self.name==other.name) and (self.address==other.address))
        else:
            return False

    def __hash__(self):
        return hash(self.__repr__())

def get_connection():
    global database_connection
    if not database_connection:
        database_connection = MySQLdb.connect('127.0.0.1', 'root', '', 'mikrotik_erp')
    return database_connection

def list_pools():
    cursor = get_connection().cursor()
    cursor.execute('select pool_name, framedipaddress from radippool')
    pools = set()
    for row in cursor:
        pools.add(Pool(row[0], row[1]))
    for pool in pools:
        print "{0:20} {1}".format(pool.name, pool.address)

def add_pool(pool_name, pool_address_range):
    conn = get_connection()
    cursor = conn.cursor()
    query = "INSERT INTO radippool (pool_name, framedipaddress, nasipaddress, calledstationid, callingstationid, username, pool_key) " + \
            "VALUES (%s, %s, '', '', '', '', '0')"
    ip_range = iplib.CIDR(pool_address_range)
    for ip in ip_range:
        cursor.execute(query, (pool_name, ip))
    conn.commit()

def rm_pool(pool_name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM radippool WHERE pool_name=%s', (pool_name,))
    conn.commit()

def list_groups():
    cursor = get_connection().cursor()
    cursor.execute("SELECT DISTINCT groupname FROM radgroupcheck ORDER BY groupname")
    for n, row in enumerate(cursor, 1):
        print "{0:2} - {1}".format(n, row[0])

def list_pool_groups(pool_name):
    cursor = get_connection().cursor()
    cursor.execute("SELECT DISTINCT groupname FROM radgroupcheck WHERE attribute='Pool-Name' AND value=%s", (pool_name, ))
    print "O pool {0} está associado aos seguintes planos:\n".format(pool_name)
    for row in cursor:
        print "  ->", row[0]
    print

def pool_add_group(pool_name):
    pass


#$ pool set-group nome-pool
#
#O pool "nome-pool" está associado aos seguintes planos:
#  1 - Plano X
#  2 - Plano Y
#  
#Grupos disponíveis:
#  1 - Plano X
#  2 - Plano Y
#  3 - Plano Z
#
#Informe o código dos grupos separados por vírgula (ex: 1, 2, 3): 1, 2


if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Freeradius pool manager - Manages pools stored in MySQL")
    subparser = parser.add_subparsers(dest='command')
    subparser.add_parser('ls')

    add_cmd = subparser.add_parser('add')
    add_cmd.add_argument('pool_name', type=str)
    add_cmd.add_argument('pool_range', type=str)

    rm_cmd = subparser.add_parser('rm')
    rm_cmd.add_argument('pool_name', type=str)

    groups_cmd = subparser.add_parser('groups')
    groups_cmd.add_argument('pool_name', type=str, nargs='?', default='')

    set_group_cmd = subparser.add_parser('set-group')
    set_group_cmd.add_argument('pool_name', type=str)
    set_group_cmd.add_argument('group_id', type=str)

    rm_group_cmd = subparser.add_parser('rm-group')
    rm_group_cmd.add_argument('pool_name', type=str)
    rm_group_cmd.add_argument('group_id', type=str)

    args = parser.parse_args();
    #print args

    if args.command=='ls':
        list_pools()
    elif args.command=='add':
        add_pool(args.pool_name, args.pool_range)
    elif args.command=='rm':
        rm_pool(args.pool_name)
    elif args.command=='groups':
        if args.pool_name!='':
            list_pool_groups(args.pool_name)
        else:
            list_groups()
    elif args.command=='set-group':
        pool_set_group(args.pool_name, args.group_id)

