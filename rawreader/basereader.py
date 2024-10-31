import logging
import re

import serial

logger = logging.getLogger(__name__)

class BaseReader:
    def read_input(self) -> str:
        raise("Not yet implemented!")


class SerialReader(BaseReader):
    def __init__(self, port: str, baudrate: int, bytesize: int=8, parity: str=serial.PARITY_NONE, stopbits: int=1, timeout: int=None) -> None:
        self._port = port
        self._baudrate = baudrate
        self._bytesize = bytesize
        self._parity = parity
        self._stopbits = stopbits
        self._timeout = timeout
        pass

    def read_input(self) -> str:
        bitstring = ""
        read_end = False
        card_inserted = False
        with serial.Serial(self._port, baudrate=self._baudrate, bytesize=self._bitcount, parity=self._parity, stopbits=self._stopbit, timeout = self._timeout) as mc_port:
            logger.debug("Waiting for card ...")
            while not read_end:
                line = mc_port.readline().decode('ascii')
                if line.startswith("debug"):
                    logger.debug(line.strip())
                if "info: read end" in line:
                    logger.debug("Reading finished")
                    # We're done
                    read_end = True
                matcher = re.match(r"info:\sbits:\s+([01]+)", line)
                if matcher:
                    bitstring = matcher.group(1)
            logger.debug("Bitstring read: %d", bitstring)
        return bitstring
