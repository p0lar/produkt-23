import logging
import re

import iso7812
from decoder.baseparser import BaseParser
from decoder.baseprinter import BasePrinter
from decoder.utils import check_luhn

from ..basedecoder import BaseDecoder

logger = logging.getLogger(__name__)

BCD5_LSB = {}
BCD5_LSB["0000"] = "0"
BCD5_LSB["1000"] = "1"
BCD5_LSB["0100"] = "2"
BCD5_LSB["1100"] = "3"
BCD5_LSB["0010"] = "4"
BCD5_LSB["1010"] = "5"
BCD5_LSB["0110"] = "6"
BCD5_LSB["1110"] = "7"
BCD5_LSB["0001"] = "8"
BCD5_LSB["1001"] = "9"
BCD5_LSB["0101"] = ":"
BCD5_LSB["1101"] = ";"
BCD5_LSB["0011"] = "<"
BCD5_LSB["1011"] = "="
BCD5_LSB["0111"] = ">"
BCD5_LSB["1111"] = "?"

BCD5_MSB = {}
BCD5_MSB["0000"] = "0"
BCD5_MSB["0001"] = "1"
BCD5_MSB["0010"] = "2"
BCD5_MSB["0011"] = "3"
BCD5_MSB["0100"] = "4"
BCD5_MSB["0101"] = "5"
BCD5_MSB["0110"] = "6"
BCD5_MSB["0111"] = "7"
BCD5_MSB["1000"] = "8"
BCD5_MSB["1001"] = "9"
BCD5_MSB["1010"] = ":"
BCD5_MSB["1011"] = ";"
BCD5_MSB["1100"] = "<"
BCD5_MSB["1101"] = "="
BCD5_MSB["1110"] = ">"
BCD5_MSB["1111"] = "?"

SC_DETAILS = {}
SC_DETAILS[1] = {}
SC_DETAILS[2] = {}
SC_DETAILS[3] = {}

# Digit 1: Interchange and technology

SC_DETAILS[1][0] = "Reserved for future use by ISO."
SC_DETAILS[1][1] = "Available for international interchange."
SC_DETAILS[1][2] = "Available for international interchange and with integrated circuit, which should be used for the financial transaction when feasible."
SC_DETAILS[1][3] = "Reserved for future use by ISO."
SC_DETAILS[1][4] = "Reserved for future use by ISO."
SC_DETAILS[1][5] = "Available for national interchange only, except under bilateral agreement."
SC_DETAILS[1][6] = "Available for national interchange only, except under bilateral agreement, and with integrated circuit, which should be used for the financial transaction when feasible."
SC_DETAILS[1][7] = "Not available for general interchange, except under bilateral agreement."
SC_DETAILS[1][8] = "Reserved for future use by ISO."
SC_DETAILS[1][9] = "Test."

# Digit 2: Authorization processing

SC_DETAILS[2][0] = "Transactions are authorized following the normal rules."
SC_DETAILS[2][1] = "Reserved for future use by ISO."
SC_DETAILS[2][2] = "Transactions are authorized by issuer and should be online."
SC_DETAILS[2][3] = "Reserved for future use by ISO."
SC_DETAILS[2][4] = "Transactions are authorized by issuer and should be online, except under bilateral agreement."
SC_DETAILS[2][5] = "Reserved for future use by ISO."
SC_DETAILS[2][6] = "Reserved for future use by ISO."
SC_DETAILS[2][7] = "Reserved for future use by ISO."
SC_DETAILS[2][8] = "Reserved for future use by ISO."
SC_DETAILS[2][9] = "Reserved for future use by ISO."

# Digit 3: Range of services and PIN requirements

SC_DETAILS[3][0] = "No restrictions and PIN required."
SC_DETAILS[3][1] = "No restrictions."
SC_DETAILS[3][2] = "Goods and services only (no cash)."
SC_DETAILS[3][3] = "ATM only and PIN required."
SC_DETAILS[3][4] = "Cash only."
SC_DETAILS[3][5] = "Goods and services only (no cash) and PIN required."
SC_DETAILS[3][6] = "No restrictions and require PIN when feasible."
SC_DETAILS[3][7] = "Goods and services only (no cash) and require PIN when feasible."
SC_DETAILS[3][8] = "Reserved for future use by ISO."
SC_DETAILS[3][9] = "Reserved for future use by ISO."

# Hash keys
SS = "start"
ES = "end"
FS = "fs"

# Sentinels for Track 1-3
sentinels = {}
sentinels[1] = {SS: "%", ES: "?", FS: "^"}
sentinels[2] = {SS: ";", ES: "?", FS: "="}
sentinels[3] = {SS: ";", ES: "?", FS: "="}

START_5 = "11010"  # ; + parity
START_7 = "010001"  # % + parity

class Decoder(BaseDecoder):

    def __init__(self, trackno) -> None:
        self._trackno = trackno # The track to use for the decoded data
        super().__init__()

    def __find_sync(self, trackno: int, data: str) -> int:
        if trackno == 1:  # Only track 1 is alphanum
            return self.__find_syncpattern(data=data, five_bit=False)
        elif trackno == 2 or trackno == 3:
            return self.__find_syncpattern(data=data, five_bit=True)
        logger.warn("Invalid track number: %d", trackno)
        return -1


    def __find_syncpattern(self, data: str, five_bit: bool = True) -> int:
        syncpattern = START_5  # Start sentinel ';' including parity
        if not five_bit:
            syncpattern = START_7
        sync_start = data.find(syncpattern)
        if sync_start < 0:
            # No sync found
            return -1

        # Return the offset for data start
        logger.debug("Start sentinel (%s) found", syncpattern)
        return sync_start


    def __decode_bits(self, offs: int, data: str, parity_odd: bool = True, five_bit: bool = True) -> str:
        is_even = data.count("1") % 2 == 0 or False
        if (parity_odd and is_even) or (not parity_odd and not is_even):
            logger.error("Parity error at offset %d", offs)

        if five_bit:
            return BCD5_LSB[data[:4]]

        # Calculate ASCII from DEC SIXBIT
        bitval = 0
        for (cnt, bit) in enumerate(reversed(data[:7])):
            # print(cnt, bit)
            if bit == "1":
                bitval += 2 ** cnt
        # print(bitval, bitval + 32, data[:7])
        return chr(bitval + 32)

    def __decode_chunk(self, trackno: int, offset: int, data: str) -> str:
        if trackno == 1:
            return self.__decode_bits(offset, data, five_bit=False)
        elif trackno == 2 or trackno == 3:
            return self.__decode_bits(offset, data, five_bit=True)
        logger.warn("Invalid track number: %d", trackno)
        return ""

    def decode_bitstring(self, bitstring: str) -> tuple:

        result = ""
        trackdata = [None, None, None]
        symbol_len = -1
        if self._trackno == 1:
            symbol_len = 7
        elif self._trackno == 2 or self._trackno == 3:
            symbol_len = 5
        else:
            logger.error("Invalid track number: %d", self._trackno)
            return ""

        data_offset = self.__find_sync(self._trackno, bitstring)
        if data_offset < 1:
            logger.warning("No sync found, maybe bitstring is not in isoformat") # -> Custom decoder?
            return ""

        logger.debug("Data starts at position %d", data_offset)

        while data_offset + symbol_len < len(bitstring):
            result += self.__decode_chunk(self._trackno, data_offset,
                                    bitstring[data_offset:data_offset+symbol_len])
            data_offset += symbol_len
            if result.endswith(sentinels[self._trackno][ES]):
                logger.debug("Data ends at position %d", data_offset + symbol_len)
                break

        trackdata[self._trackno - 1] = result
        return tuple(trackdata)

class Parser(BaseParser):
    def process_trackdata(self, trackdata: tuple) -> tuple:
        track_details = [None, None, None]
        for (trackno, data) in enumerate(trackdata, 1):
            result = None
            if data is None:
                logger.warn("No data for track %d", trackno)
                continue
            if trackno == 1:
                # r"^%B([0-9]{1,19})\^([^\^]{2,26})\^([0-9]{4}|\^)([0-9]{3}|\^)([^\?]*)\?$"
                matcher = re.match(r"^%(?P<FC>[A-Z])(?P<PAN>[0-9]{1,19})\^(?P<CC>[0-9]{3})?(?P<NM>[^\^]{2,26})\^(?P<ED>[0-9]{4}|\^)(?P<SC>[0-9]{3}|\^)(?P<PVV>[0-9]{5})(?P<DD>[^\?]*)\?$", data)
                if not matcher:
                    logger.warn("Non-ISO 7813 track 1 format: '%s'", data)
                    continue
                logger.debug("ISO 7813 track 1 data: %s", data)
                result = {
                    "trackno" : 1, # inline signal track
                    "FC": matcher.group("FC"), # Format code
                    "PAN": matcher.group("PAN"), # Primary account number
                    "CC" : matcher.group("CC"), # Country code
                    "NM": matcher.group("NM"), # Name
                    "ED" : matcher.group("ED"), # Expiry data
                    "SC" : matcher.group("SC"), # Service code
                    "PVV" : matcher.group("PVV"), # PIN verification value
                    "DD" : matcher.group("DD") # Discretionary data
                }
            elif trackno == 2:
                # matcher = re.match(r"\;(.+)\?", data) # use sentinels
                # if not matcher:
                #     logger.warn("No ISO string found?")
                #     return
                # # fields = matcher.group(1).split(sentinels[trackno][FS])

                matcher = re.match(r"^\;(?P<PAN>[0-9]{1,19})\=(?P<ED>[0-9]{4}|\=)(?P<SC>[0-9]{3}|\=)(?P<PVV>[0-9]{5})(?P<DD>[^\?]*)\?$", data)
                if not matcher:
                    logger.warn("Non-ISO 7813 track 2 format: '%s'", data)
                    continue
                logger.debug("ISO 7813 track 2 data: %s", data)
                # matcher = re.match(r"^\;([0-9]{1,19})\=([^\?]*)\?$")

                # CCED = matcher.group("CCED") # Countrycode does not have a field separator if it's not there (pan starts with 59, mastercard)
                # CC = None
                # ED = None
                # if len(CCED) == 3:
                #     CC = int(CCED)
                # elif len(CCED) == 4:
                #     ED = int(CCED)
                # elif len(CCED) == 7:
                #     CC = int(CCED[:3])
                #     ED = int(CCED[:4])
                result = {
                    "trackno" : 2, # inline signal track
                    "PAN": matcher.group("PAN"), # Primary account number
                    "CC" : None, # Country code
                    "ED" : matcher.group("ED"), # Expiry data
                    "SC" : matcher.group("SC"), # Service code
                    "PVV" : matcher.group("PVV"), # PIN verification value
                    "DD" : matcher.group("DD") # Discretionary data
                }

            track_details[trackno - 1] = result
        return tuple(track_details)

class Printer(BasePrinter):

    def print_trackdata(self, track_details: tuple):
        for (trackno, data) in enumerate(track_details, 1):
            if trackno == 3:
                break
            if data is None:
                print(f"No details for track {trackno}")
                continue

            print(f"Details for track {trackno} =====================================")
            if trackno == 1:
                self.__print_track1_data(data, sc_details=self._print_verbose, pan_details=self._print_verbose)
            if trackno == 2:
                self.__print_track2_data(data, sc_details=self._print_verbose, pan_details=self._print_verbose)
            # else:
            #    print(f"Printing details for track {trackno} not yet implemented")

    def __print_track1_data(self, data: dict, pan_details: bool=False, sc_details: bool=False):
        print(f"Primary account number: {data['PAN']} (valid: {check_luhn(data['PAN'])})")
        if pan_details:
            iso7812.print_pan_details(data['PAN'])
        print(f"Name:                  '{data['NM']}'")
        if self._print_verbose and not " /" == data['NM']:
            # Print name details
            name_matcher = re.match(r"^(?P<SURNAME>[^\/]+)\/?(?P<FIRSTNAME>[^\.]*)(?P<TITLE>[\.]*)$", data["NM"])

            print(f"  Surname:         {name_matcher['SURNAME']}")
            print(f"  Firstname:       {name_matcher['FIRSTNAME']}")
            print(f"  Title:           {name_matcher['TITLE']}")

        print(f"Country code:           {data['CC']}")
        print(f"Expiry date (YYMM):     {data['ED']}")
        print(f"Serice code:            {data['SC']}")
        if sc_details:
            for (i, digit) in enumerate(str(data['SC']), 1):
                print(f"  Digit {i}: {digit} -> {SC_DETAILS[i][int(digit)]}")
        print(f"PIN verification value: {data['PVV']}")
        print(f"Discretionary data:     {data['DD']}")

    def __print_track2_data(self, data: dict, pan_details: bool=False, sc_details: bool=False):
        print(f"Primary account number: {data['PAN']} (valid: {check_luhn(data['PAN'])})")
        if pan_details:
            iso7812.print_pan_details(data['PAN'])
        print(f"Country code:           {data['CC']}")
        print(f"Expiry date (YYMM):     {data['ED']}")
        print(f"Serice code:            {data['SC']}")
        if sc_details:
            for (i, digit) in enumerate(str(data['SC']), 1):
                print(f"  Digit {i}: {digit} -> {SC_DETAILS[i][int(digit)]}")
        print(f"PIN verification value: {data['PVV']}")
        print(f"Discretionary data:     {data['DD']}")

