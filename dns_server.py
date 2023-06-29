from dnslib import DNSRecord, QTYPE, RD, SOA, DNSHeader, RR, A
from dns.resolver import Resolver
import socket
import logging
import time
import json
import threading

class DFATree():
    def __init__(self,ttl) -> None:
        self.ttl=ttl
        self.tree = dict()

    def add(self, domain, ip, *lastTime:float):
        position = self.tree
        for letter in list(domain):
            if letter in position:
                position = position[letter]
            else:
                position[letter] = dict()
                position = position[letter]
        position['isEnd'] = True
        if lastTime:
            position['lastTime']=lastTime[0]
        else:
            position['lastTime']=time.time()
        position['ip']=ip
        with open('dict.json','w') as f:
            json.dump(self.tree,f)
        return self.tree

    def check(self, domain):
        position = self.tree
        for letter in list(domain):
            if letter in position:
                position = position[letter]
            else:
                return False
        if position.get('isEnd') == None:
            return False
        if time.time()-position['lastTime']>=self.ttl:
            return False
        return position['ip']

dns_tree=DFATree(6000)
dns_resolver = Resolver()
dns_resolver.nameservers = ["8.8.8.8", "8.8.4.4"]
logging.basicConfig(level=logging.DEBUG,
                    filename='dns.log',
                    filemode='w',
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'
                    )

def read_record():
    with open('dict.json','r') as f:
        try:
            dns_tree.tree=json.load(f)
        except:
            pass
    with open('record','r') as f:
        records=f.readlines()
    for record in records:
        record=record.split('  ')#domain和ip之间用两个Space分隔
        dns_tree.add(record[0],record[1],float(record[2].strip('\n')))

def _dns_handler(udp_sock, message, address):
    try:
        return dns_handler(udp_sock, message, address)
    except Exception as e:
        logging.error(e)

def get_ip_from_domain(domain):
    domain = domain.lower().strip()
    try:
        return dns_resolver.resolve(domain, 'A')[0].to_text()
    except:
        return None


def reply_for_not_found(income_record):
    header = DNSHeader(id=income_record.header.id,
                       bitmap=income_record.header.bitmap, qr=1)
    header.set_rcode(0)
    record = DNSRecord(header, q=income_record.q)
    return record


def reply_for_A(income_record, ip, ttl=60):
    r_data = A(ip)
    header = DNSHeader(id=income_record.header.id,
                       bitmap=income_record.header.bitmap, qr=1)
    domain = income_record.q.qname
    query_type_int = QTYPE.reverse.get('A') or income_record.q.qtype
    record = DNSRecord(header, q=income_record.q, a=RR(
        domain, query_type_int, rdata=r_data, ttl=ttl))
    return record


def dns_handler(s, message, address):
    try:
        income_record = DNSRecord.parse(message)
    except:
        logging.error('     %s解析错误' % address)
        return
    try:
        qtype = QTYPE.get(income_record.q.qtype)
    except:
        qtype = 'unknown'
    domain = str(income_record.q.qname).strip('.')
    info = '%s -- %s, from %s' % (qtype, domain, address)
    if qtype == 'A':
        cache=dns_tree.check(domain)
        if cache !=False:
            ip = cache
            response = reply_for_A(income_record, ip=ip, ttl=60)
            s.sendto(response.pack(), address)
            return logging.info(info+'  By cache.')
        ip = get_ip_from_domain(domain)
        if ip:
            response = reply_for_A(income_record, ip=ip, ttl=60)
            s.sendto(response.pack(), address)
            dns_tree.add(domain,ip)
            return logging.info(info)
    response = reply_for_not_found(income_record)
    s.sendto(response.pack(), address)
    logging.info(info)
    return


if __name__ == '__main__':
    read_record()
    logging.info('记录读取完毕')
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.bind(('127.0.0.1', 53))
    logging.info('DNS服务器启动')
    while True:
        message, address = udp_sock.recvfrom(512)
        t=threading.Thread(target=_dns_handler,args=(udp_sock, message, address))
        t.start()
