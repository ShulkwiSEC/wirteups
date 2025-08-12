## TZe-611 (misc) — (WhyCTF 2025) Writeup


#### What this challenge is about

* **Given**: a Bluetooth HCI snoop log `btsnoop_hci.log` (H4 UART).
* **Observation**: it contains a Classic BT connection with L2CAP → RFCOMM → SPP traffic.
  The SPP payload looks like commands for a Brother P-touch label printer.
  The challenge name “TZe-611” hints at Brother TZe tape.
* **Goal**: reconstruct what was printed.
  The printed output is a raster image containing the flag directly.

---

#### overview
*in the first senario, i was think it will be qr code image and i need to extract it and decode it to get the flag but, naaah*
so you after digging into the capture The capture contains an RFCOMM/Serial Port session to a Brother label printer.
* Brother P-touch printers use ESC/P-style commands; `ESC i S` selects raster mode, and repeated `G <len> <len> <data>` lines contain PackBits-compressed bitmap rows.
(see [ESC/P-Style commands](https://download.brother.com/welcome/docp000584/cv_pt9700_eng_escp_103.pdf) for details)

![xdd: bytes of data](image.png "xdd: bytes of data" )

*now it make sence cuz The challenge name “TZe-611” hints at Brother TZe tape.*

![tze tape](https://m.media-amazon.com/images/I/61KhXIcC1JL._AC_SX679_.jpg "tze tape")

*The printed output is a raster image containing the flag directly.*
* so we can try Rendering them in order reconstructs exactly what the printer would have printed — `the flag label`.
---

#### plan to solve it

1. **Inspect the protocol hierarchy** and confirm SPP/RFCOMM traffic:

```bash
tshark -r ./btsnoop_hci.log -q -z io,phs
```

2. **Extract all SPP payload bytes** to a binary file:

```bash
tshark -r ./btsnoop_hci.log -Y btspp -T fields -e btspp.data \
  | tr -d ':\n' | xxd -r -p > spp.bin
```

3. **Reconstruct the raster image**:

* The SPP stream starts with `ESC i S` and then many `G` records.
  Each `G` record represents one raster line, PackBits-compressed.
* Decompress all `G` lines and stack them vertically to form a 1-bit monochrome image.
* I used a helper script (`solve.py`) to automate this:

```bash
python3 solve.py
# outputs: label.png
```

* The generated PNG clearly shows the flag text printed on the label.
---

## REFERENCES
- ESC/P-Style commands: https://download.brother.com/welcome/docp000584/cv_pt9700_eng_escp_103.pdf
- PackBits: https://en.wikipedia.org/wiki/PackBits
