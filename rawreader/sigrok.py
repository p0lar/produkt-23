import csv
import logging
from . import basereader

logger = logging.getLogger(__name__)

class CsvReader(basereader.BaseReader):

    def __init__(self, fh) -> None:
        super().__init__()
        self._fh = fh

    def read_input(self) -> tuple:
        rdr = csv.DictReader(self._fh)
        lineno = 0
        lastline = None
        bitstring = ""
        for line in rdr:
            lineno += 1
            if lastline is None:
                lastline = line
                continue

            if lastline["CRD"] == "1": # No card inserted, negative logic
                continue

            if (lastline["RCP"] == "1" and line["RCP"] == "0"): # Negative clock edge
                if (line["RDP"] == "1"): # Negative logic
                    bitstring += "0"
                else:
                    bitstring += "1"

            lastline = line

        logger.debug("Read %d lines", lineno)
        logger.debug("Bits read: '%s'", bitstring)
        return bitstring
