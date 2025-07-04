from dnslib import DNSRecord, DNSHeader, DNSQuestion, RR, A, QTYPE
from dnslib.server import DNSServer, BaseResolver
import socket

# List of domains to redirect to localhost
redirect_domains = [
    "example.com",
    "blocked-site.net",
    "test.local"
]

# Default upstream DNS server (use Windows DNS automatically)
import dns.resolver
default_dns = dns.resolver.get_default_resolver().nameservers[0]  # E.g. '192.168.1.1'

class CustomResolver(BaseResolver):
    def resolve(self, request, handler):
        qname = str(request.q.qname).rstrip('.')
        qtype = QTYPE[request.q.qtype]
        print(f"Query: {qname} ({qtype})")

        # Check if domain is in redirect list
        if any(qname.endswith(domain) for domain in redirect_domains):
            print(f"Redirecting {qname} to localhost")
            reply = request.reply()
            reply.add_answer(RR(qname, QTYPE.A, rdata=A("127.0.0.1"), ttl=60))
            return reply
        else:
            try:
                # Forward to default DNS
                proxy_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                proxy_sock.settimeout(2)
                proxy_sock.sendto(request.pack(), (default_dns, 53))
                data, _ = proxy_sock.recvfrom(4096)
                return DNSRecord.parse(data)
            except Exception as e:
                print(f"DNS forward error: {e}")
                reply = request.reply()
                return reply

# Start the DNS server
resolver = CustomResolver()
server = DNSServer(resolver, port=53, address="0.0.0.0", tcp=False)
print("DNS server running on port 53...")
server.start()