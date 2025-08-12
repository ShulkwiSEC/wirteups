#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from PIL import Image
from collections import Counter

WORKDIR = Path(__file__).resolve().parent
PCAP_PATH = WORKDIR / "btsnoop_hci.log"
OUT_IMG_PATH = WORKDIR / "label.png"

def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        sys.exit(f"[!] Command failed: {cmd}\n{r.stderr}")
    return r.stdout

def extract_spp(pcap):
    out = run(["tshark", "-r", str(pcap), "-Y", "btspp", "-T", "fields", "-e", "btspp.data"])
    data = bytes.fromhex(out.replace(":", "").replace("\n", "").strip())
    if not data:
        sys.exit("[!] No SPP payload found")
    return data

def packbits(data):
    out, i, n = bytearray(), 0, len(data)
    while i < n:
        c = data[i]; i += 1
        if c <= 0x7F:
            out.extend(data[i:i+c+1]); i += c+1
        elif c != 0x80:
            out.extend([data[i]] * (257-c)); i += 1
    return bytes(out)

def parse_lines(spp):
    lines, i, n = [], 0, len(spp)
    sidx = spp.find(b"\x1b\x69\x53")
    if sidx != -1: i = sidx
    while i+3 <= n:
        if spp[i] == 0x47:
            length = spp[i+1] | (spp[i+2] << 8)
            end = i+3+length
            if length and end <= n:
                lines.append(packbits(spp[i+3:end]))
                i = end; continue
        i += 1
    if not lines:
        sys.exit("[!] No raster lines found")
    w = Counter(len(l) for l in lines).most_common(1)[0][0]
    return [l for l in lines if len(l) == w]

def render(lines, path):
    w, h = len(lines[0])*8, len(lines)
    Image.frombytes("1", (w, h), b"".join(lines)).save(path)
    print(f"[+] Image saved: {path} ({w}x{h})")

if __name__ == "__main__":
    print("[+] Extracting SPP payload...")
    spp = extract_spp(PCAP_PATH)
    print(f"[+] {len(spp)} bytes extracted")
    lines = parse_lines(spp)
    print(f"[+] {len(lines)} lines parsed")
    render(lines, OUT_IMG_PATH)
