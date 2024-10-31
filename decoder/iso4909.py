import logging
import re
from datetime import datetime

import iso7812
from decoder.baseparser import BaseParser
from decoder.baseprinter import BasePrinter
from decoder.utils import check_luhn

logger = logging.getLogger(__name__)


def format_code(code: str) -> str:
    if code == "00":
        return "Invalid for international interchange."
    elif code == "01":
        return "The layout shall conform to Table 1 of this International Standard."
    elif code == "02":
        return "The layout shall conform to Table 2 of this International Standard."
    elif code >= "03" and code <= "89":
        return "Reserved for future use by ISO."
    return "Available for use by individual card issuers but not for international interchange."


def cl_details(code: str) -> str:
    if code >= "00" and code <= "79":
        return "Number of days."
    elif code == "80":
        return "Cycle begin each 7 days."
    elif code == "81":
        return "Cycle begin each 14 days."
    elif code == "82":
        return "Cycle begins each 1st and 15th days of every month."
    elif code == "83":
        return "Cycle begins the day of the month specified in CB of every month."
    elif code == "84":
        return "Cycle begins the day of the month specified in CB of every third month."
    elif code == "85":
        return "Cycle begins the day of the month specified in CB of every sixth month."
    elif code == "86":
        return "Cycle begins the day of the year specified in CB of every year."
    elif code == "87" or code == "88" or code == "89":
        return "Reserved for future use by ISO/TC 68."
    else:
        return "Reserved for proprietary use of card issuer, but not for international interchange."


def ic_details(code: str) -> str:
    if code >= "00" and code <= "79":
        return "Number of days."
    elif code == "0":
        return "No restriction."
    elif code == "1":
        return "Not available for international interchange."
    elif code >= "2" and code <= "8":
        return "Limited interchange, only local use and under agreement."
    else:
        return "Limited interchange, recommended for test cards."


def sr_details(code: str) -> str:
    digit1 = code[0]
    digit2 = code[1]
    result = ""

    if digit1 == "0":
        result += "Associated account number not encoded on track"
    elif digit1 == "1":
        result += "Savings account"
    elif digit1 == "2":
        result += "Current or checking account"
    elif digit1 == "3":
        result += "Credit card account"
    elif digit1 == "4":
        result += "Generic or universal account"
    elif digit1 == "5":
        result += "Interest-bearing current or checking account"
    elif digit1 >= "6" and digit1 <= "8":
        result += "Reserved for future use by ISO/TC 68"
    else:
        result += "Reserved for card issuer's internal use, not for interchange"

    result += ", "

    if digit2 == "0":
        result += "No restrictions."
    elif digit2 == "1":
        result += "No cash dispense."
    elif digit2 == "2":
        result += "No point of sale (POS) transaction."
    elif digit2 == "3":
        result += "No cash dispense and no POS transaction."
    elif digit2 == "4":
        result += "Authorization required."
    elif digit2 >= "6" and digit2 <= "7":
        result += "Reserved for future use by ISO/TC 68."
    else:
        result += "Reserved for card issuer's internal use, only local use and under agreement."

    return result


def cb_details(code: str, expiry: str) -> datetime:
    if expiry == "=":
        return None
    if code == "0000":  # No cycle, placeholder
        return None
    expiry_date = datetime.strptime(expiry, "%y%m")
    year_in_century = code[0]
    days_in_year = code[1:]
    start_year = expiry_date.year - \
        (expiry_date.year % 10) + int(year_in_century)
    if start_year > expiry_date.year:  # decade changed
        start_year -= 10
    cycle_begin = datetime.strptime(f"{start_year}{days_in_year}", "%Y%j")
    return cycle_begin


def rm_details(code: str) -> str:
    if code == "0":
        return "Include AD and DD fields in transactions messages."
    elif code == "1":
        return "Do not include AD field in transactions messages."
    elif code == "2":
        return "Do not include DD field in transactions messages."
    return "Invalid."


def pincp_details(code: str, fc: str) -> str:
    if fc == "01":
        a_type = code[:2]
        pin_offset = code[2:]
        algo = "Reserved for future use by ISO/TC 68"
        if a_type >= "00" and a_type <= "09":
            algo = "Private"
        elif a_type >= "10" and a_type <= "19":
            algo = "DEA"
        return f"Algorithm: {algo}, PIN offset: {pin_offset}"
    elif fc == "02":
        a_type = code[0]
        a_key = code[1]
        pin_offset = code[2:]
        algo = "Reserved for future use by ISO/TC 68"
        if a_type == "0":
            algo = "Private"
        elif a_type == "1":
            algo = "DEA"
        return f"Algorithm: {algo}, Algorithm key/seed: {a_key}, PIN offset: {pin_offset}"
    return "No details"


def cscn_details(code: str) -> str:
    algo = code[0]
    algo_detail = ""
    vv = code[0:]

    if algo >= "0" and algo <= "4":
        algo_detail = "National use"
    elif algo >= "5" and algo <= "8":
        algo_detail = "International security methods given by ISO/TC 68"
    elif code == "9":
        algo_detail = "Private use"

    return f"Algorithm: {algo_detail}, verification value: {vv}"


class Parser(BaseParser):
    def process_trackdata(self, trackdata: tuple) -> tuple:
        track_details = [None, None, None]
        for (trackno, data) in enumerate(trackdata, 1):
            if trackno != 3:
                continue
        result = None
        if data is None:
            logger.warn("No data for track %d", trackno)
            return tuple(track_details)
        matcher = re.match(r"^\;(?P<FC>[0-9]{2})(?P<PAN>[0-9]{1,19})?\=(?P<CC>[0-9]{3}\=)(?P<CuC>[0-9]{3})(?P<CE>[0-9]{5})(?P<AA>[0-9]{4})(?P<AR>[0-9]{4})(?P<CB>[0-9]{4})(?P<CL>[0-9]{2})(?P<RC>[0-9]{1})(?P<PINCP>[0-9]{6}|\=)(?P<IC>[0-9]{1})(?P<PANSR>[0-9]{2})(?P<FSANSR>[0-9]{2})(?P<SSANSR>[0-9]{2})(?P<ED>[0-9]{4}|\=)(?P<CSN>[0-9]{1})(?P<CScN>[0-9]{9}|\=)(?P<FSAN>[0-9]*)\=(?P<SSAN>[0-9]*)\=(?P<RM>[0-9]{1})(?P<CCD>[0-9]{6}|\=)(?P<AD>[^\?]*)\?$", data)
        if not matcher:
            logger.warn("Non-ISO 4909 track 3 format: '%s'", data)
            return tuple(track_details)
        result = {
            "trackno": 3,  # inline signal track
            "FC": matcher.group("FC"),  # Format code
            "PAN": matcher.group("PAN"),  # Primary account number
            "CC": matcher.group("CC"),  # Country code
            "CuC": matcher.group("CuC"),  # Currency code
            "CE": matcher.group("CE"),  # Currency exponent
            "AA": matcher.group("AA"),  # Amount authorized (per cycle)
            "AR": matcher.group("AR"),  # Amount remaining (this cycle)
            "CB": matcher.group("CB"),  # Cycle begin (YDDD)
            "CL": matcher.group("CL"),  # Cycle length
            "RC": matcher.group("RC"),  # Retry count
            "PINCP": matcher.group("PINCP"),  # PIN control parameters
            "IC": matcher.group("IC"),  # Interchange control
            "PANSR": matcher.group("PANSR"),  # PAN service restriction
            "FSANSR": matcher.group("FSANSR"),  # FSAN service restriction
            "SSANSR": matcher.group("SSANSR"),  # SSAN service restriction
            "ED": matcher.group("ED"),  # Expiry data
            "CSN": matcher.group("CSN"),  # Card sequence number
            "CScN": matcher.group("CScN"),  # Card security number
            "FSAN": matcher.group("FSAN"),  # First Subsidiary Account Number
            "SSAN": matcher.group("SSAN"),  # Second Subsidiary Account Number
            "RM": matcher.group("RM"),  # Relay marker
            "CCD": matcher.group("CCS"),  # Crypto check digit
            "AD": matcher.group("AD"),  # Additional data
        }

        track_details[trackno - 1] = result
        return tuple(track_details)


class Printer(BasePrinter):
    def print_trackdata(self, track_details: tuple):
        for (trackno, data) in enumerate(track_details, 1):
            if trackno != 3:
                break
            if data is None:
                print(f"No details for track {trackno}")
                continue

            print(f"Details for track {
                  trackno} =====================================")
            print(f"Format code:            {data['FC']}")
            if self._print_verbose:
                print(f"  ->                   {format_code(data['FC'])}")
            print(f"Primary account number:         {
                  data['PAN']} (valid: {check_luhn(data['PAN'])})")
            if self._print_verbose:
                iso7812.print_pan_details(data['PAN'])
            print(f"County code:                    {data['CC']}")
            print(f"Currency code:                  {data['CuC']}")
            print(f"Currency exponent:              {data['CE']}")
            print(f"Amount authorized (per cycle):  {data['AA']}")
            print(f"Amount remaining (this cycle):  {data['AR']}")
            print(f"Cycle begin (YDDD):             {data['CB']}")
            if self._print_verbose:
                print(
                    f"  ->                   {cb_details(data['IC'], data['ED'])}")
            print(f"Cycle length:                   {data['CL']}")
            print(f"Retry count:                    {data['RC']}")
            print(f"PIN control parameters:         {data['PINCP']}")
            print(f"Interchange control:            {data['IC']}")
            if self._print_verbose:
                print(f"  ->                   {ic_details(data['IC'])}")
            print(f"PAN service restiction:         {data['PANSR']}")
            print(f"FSAN service restiction:        {data['FSANSR']}")
            print(f"SSAN service restiction:        {data['SSANSR']}")
            print(f"Expiry data (YYMM):             {data['ED']}")
            print(f"Card sequence number:           {data['CSN']}")
            print(f"Card security number:           {data['CScN']}")
            print(f"First subsidiary accnt:         {data['FSAN']}")
            print(f"Second subsidiary accnt:        {data['SSAN']}")
            print(f"Relay marker:                   {data['RM']}")
            print(f"Crypto check digit:             {data['CCS']}")
            print(f"Additional data:                {data['AD']}")
