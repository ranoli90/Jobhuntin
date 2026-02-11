import socket

HOST = "zglovpfwyobbbaaocawz.supabase.co"
PORTS = [5432, 6543, 5433]

for port in PORTS:
    print(f"Checking {HOST}:{port}...")
    try:
        with socket.create_connection((HOST, port), timeout=5) as sock:
            print(f"OPEN: {HOST}:{port}")
    except Exception as e:
        print(f"CLOSED/ERROR: {HOST}:{port} ({e})")
