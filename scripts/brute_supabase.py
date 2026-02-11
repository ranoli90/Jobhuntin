import socket

PROJECT_REF = "zglovpfwyobbbaaocawz"
SUBDOMAINS = ["db", "pooler", "postgres", "direct"]
DOMAINS = ["supabase.co", "supabase.com"]

print(f"Brute-forcing subdomains for {PROJECT_REF}...")

for sub in SUBDOMAINS:
    for dom in DOMAINS:
        host = f"{sub}.{PROJECT_REF}.{dom}"
        try:
            ip = socket.gethostbyname(host)
            print(f"FOUND: {host} -> {ip}")
        except:
            pass

# Also try the project ref as subdomain directly
for dom in DOMAINS:
    host = f"{PROJECT_REF}.{dom}"
    try:
        ip = socket.gethostbyname(host)
        print(f"FOUND: {host} -> {ip}")
    except:
        pass
