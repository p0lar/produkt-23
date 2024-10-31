import csv

from . import basereader


class FirstLine(basereader.BaseReader):

    def __init__(self, fh) -> None:
        super().__init__()
        print()
        self._fh = fh

    def read_input(self) -> tuple:
        return self._fh.readline().strip()

def read_sigrok_csv(fh) -> str:
    reader = csv.DictReader(fh)
    lineno = 0
    lastline = None
    # bit_array = []
    bitstring = ""
    for line in reader:
        lineno += 1
        if lastline is None:
            lastline = line
            continue

        if lastline["CRD"] == "1": # No card inserted, negative logic
            continue

        if (lastline["RCP"] == "1" and line["RCP"] == "0"): # Negative clock edge
            if (line["RDP"] == "1"): # Negative logic
                # bit_array.append("0")
                bitstring += "0"
            else:
                # bit_array.append("1")
                bitstring += "1"

        lastline = line

    print(f"Read {lineno} lines")

    # Fetch the bytes
    # for offs in range(0, len(bit_array), 8):
    #     bits = "".join(bit_array[offs:offs+8])
    #     bitstring += bits

    print(f"Bits read: '{bitstring}'")
    return bitstring

# def read_serial(port, baudrate=9600, bitcount=8, parity=serial.PARITY_NONE, stopbit=1) -> str:
#     bitstring = ""
#     read_end = False
#     card_inserted = False
#     with serial.Serial(port, baudrate=baudrate, bytesize=bitcount, parity=parity, stopbits=stopbit, timeout = 1) as mc_port:
#         print("Waiting for card ...")
#         while not read_end:
#             line = mc_port.readline().decode('ascii')
#             if line.startswith("debug"):
#                 print("debug", line.strip())
#             if "info: read end" in line:
#                 print("Reading finished")
#                 # We're done
#                 read_end = True
#             matcher = re.match(r"info:\sbits:\s+([01]+)", line)
#             if matcher:
#                 bitstring = matcher.group(1)
#         print(f"Bitstring read: {bitstring}")

#     return bitstring
