import socket
import struct
import pickle
import time

TTL = 10
Local_server = '127.0.0.1'
Authoritative_server = '8.8.8.8'
Port = 53


class Cache:
    def __init__(self, data):
        self.data = data
        self.timestamp = time.time()

    def ttl_end(self):
        return time.time() - self.timestamp > TTL


cache = dict()

try:
    with open('cache.pickle', 'rb') as f:
        cache = pickle.load(f)
except FileNotFoundError:
    pass

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((Local_server, Port))

print('Server is working')


def parse_packet(packet):
    dns_header = struct.unpack('!HHHHHH', packet[:12])
    id = dns_header[0]
    qr = (dns_header[1] >> 15) & 1
    opcode = (dns_header[1] >> 11) & 15
    aa = (dns_header[1] >> 10) & 1
    tc = (dns_header[1] >> 9) & 1
    rd = (dns_header[1] >> 8) & 1
    ra = (dns_header[1] >> 7) & 1
    z = (dns_header[1] >> 4) & 7
    rcode = dns_header[1] & 15
    qdcount = dns_header[2]
    ancount = dns_header[3]
    nscount = dns_header[4]
    arcount = dns_header[5]

    offset = 12
    questions = []
    for _ in range(qdcount):
        question, offset = parse_question(packet, offset)
        questions.append(question)

    answers = []
    for _ in range(ancount):
        answer, offset = parse_answer(packet, offset)
        answers.append(answer)

    return {
        'id': id,
        'qr': qr,
        'opcode': opcode,
        'aa': aa,
        'tc': tc,
        'rd': rd,
        'ra': ra,
        'z': z,
        'rcode': rcode,
        'qdcount': qdcount,
        'ancount': ancount,
        'nscount': nscount,
        'arcount': arcount,
        'questions': questions,
        'answers': answers
    }


def parse_question(packet, offset):
    qname_parts = []
    while True:
        length = packet[offset]
        if length == 0:
            break
        qname_parts.append(packet[offset + 1: offset + length + 1].decode('utf-8'))
        offset += length + 1

    qname = '.'.join(qname_parts)
    qtype, qclass = struct.unpack('!HH', packet[offset + 1: offset + 5])
    return {
               'qname': qname,
               'qtype': qtype,
               'qclass': qclass
           }, offset + 5


def parse_answer(packet, offset):
    name_parts = []
    while True:
        length = packet[offset]
        if length >= 192:
            offset += 2
            break
        name_parts.append(packet[offset + 1: offset + length + 1].decode('utf-8'))
        offset += length + 1

    name = '.'.join(name_parts)
    rtype, rclass, ttl, rdlength = struct.unpack('!HHIH', packet[offset: offset + 10])
    rdata = packet[offset + 10: offset + 10 + rdlength]
    offset += 10 + rdlength

    return {
               'name': name,
               'type': rtype,
               'class': rclass,
               'ttl': ttl,
               'rdlength': rdlength,
               'rdata': rdata
           }, offset


def print_dns_packet(dns_packet):
    print('Header:')
    print(f"ID:{dns_packet['id']} | QR:{dns_packet['qr']} | Opcode:{dns_packet['opcode']} | AA:{dns_packet['aa']} "
          f"| TC:{dns_packet['tc']} | RD:{dns_packet['rd']} | RA:{dns_packet['ra']} | Z:{dns_packet['z']} "
          f"| RCODE:{dns_packet['rcode']} | QDCOUNT:{dns_packet['qdcount']} | ANCOUNT:{dns_packet['ancount']} "
          f"| NSCOUNT:{dns_packet['nscount']} | ARCOUNT:{dns_packet['arcount']}")

    print('Questions:')
    for question in dns_packet['questions']:
        print(f"QNAME: {question['qname']} | QTYPE:{question['qtype']} | QCLASS:{question['qclass']}")

    print('Answers:')
    for answer in dns_packet['answers']:
        print(f"NAME:{answer['name']} | TYPE:{answer['type']} | CLASS:{answer['class']} | TTL:{answer['ttl']}"
              f" | RDLENGTH:{answer['rdlength']} | RDATA:{answer['rdata']}")


while True:
    try:
        expired_entries = [key for key in cache.keys() if cache[key].ttl_end()]
        for key in expired_entries:
            del cache[key]
        data, addr = sock.recvfrom(1024)
        request = data.decode().strip()[2:]
        if request in cache and not cache[request].ttl_end():
            response = cache[request].data
            print('Record found in cache:', request, '->\n', response)
            print('')
        else:
            upstream_server = (Authoritative_server, Port)
            upstream_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            upstream_sock.sendto(data, upstream_server)
            response, _ = upstream_sock.recvfrom(2048)
            cache[request] = Cache(response)
            print('Record added to cache:', request, '->\n', response)
            print('')

        request_packet = parse_packet(data)
        response_packet = parse_packet(response)
        print('Request packet')
        print_dns_packet(request_packet)
        print('==================================')
        print('Response packet')
        print_dns_packet(response_packet)
        print('======================================================================================================')

        sock.sendto(response, addr)

        with open('cache.pickle', 'wb') as f:
            pickle.dump(cache, f)
    except ConnectionResetError:
        continue
