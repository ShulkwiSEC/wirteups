<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: #c9d1d9;
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 20px;
  }
  h1 { border-bottom: 1px solid #1c86ffff; padding-bottom: 10px; }
  strong { color: #f0f6fc; }
  code { background-color: #161b22; padding: 2px 4px; border-radius: 4px; color: #ff7b72; }
  img {
    width: 100%;
    max-width: 100%;
    margin: 20px 0;
    border-radius: 8px;
    border: 1px solid #30363d;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    display: block;
  }
  /* Fix for large screenshots looking weird */
  p { margin-bottom: 16px; }
</style>

# Beneath The Surface- bsides algiers 2025

We started by discovering a **Local File Inclusion (LFI)** vulnerability, which allowed us to download the server binary (`chall`) and a core dump (`dump.bin`). Reverse engineering the binary showed that commands needed to be signed with a specific RSA key and sent to a hidden, randomly generated URL path. Analyzing `dump.bin` revealed a huge public exponent `e`, so we used **Wiener's Attack** to instantly recover the private key `d`, allowing us to sign our own commands. 

<img src="images/screenshot_for_wiener_attack.png" alt="Wiener's Attack Success">

To find the hidden path, we leveraged the LFI again to perform a live memory leak. By reading `/proc/self/maps`, we located the process's Heap, and then used the server's `Offset` header to read that exact memory region via `/proc/self/mem`, revealing the secret 128-character execution path.

<img src="images/screenshot_for_memory_leak.png" alt="Memory Leak & Path Discovery">

With the path and private key, we achieved **Blind RCE**, but seeing no output was frustrating. To solve this, I wrote a wrapper script (`shell.sh`) that redirects command output to a temp file (`cmd > /tmp/out`) and immediately reads it back using the LFI, effectively creating a fully interactive shell to capture the flag.

<img src="images/shell.png" alt="Interactive Shell In Action">

writeup by [shulkwi](https://github.com/shulkwisec/writeups/beneath-the-surface)