import socket

HOST = "db.zglovpfwyobbbaaocawz.supabase.co"

print(f"Checking {HOST}...")
try:
    ip = socket.gethostbyname(HOST)
    print(f"IPv4: {ip}")
except socket.gaierror as e:
    print(f"IPv4 Error: {e}")

try:
    info = socket.getaddrinfo(HOST, None)
    for res in info:
        print(f"Address: {res[4]}")
except socket.gaierror as e:
    print(f"getaddrinfo Error: {e}")
