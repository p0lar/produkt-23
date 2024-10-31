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
    bitstring = ""
    for line in reader:
        lineno += 1
        if lastline is None:
            lastline = line
            continue

        if lastline["CRD"] == "1":  # No card inserted, negative logic
            continue

        if (lastline["RCP"] == "1" and line["RCP"] == "0"):  # Negative clock edge
            if (line["RDP"] == "1"):  # Negative logic
                bitstring += "0"
            else:
                bitstring += "1"

        lastline = line

    print(f"Read {lineno} lines")

    print(f"Bits read: '{bitstring}'")
    return bitstring
