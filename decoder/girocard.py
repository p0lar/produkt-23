import logging
import re

import iso7812
from decoder.baseparser import BaseParser
from decoder.baseprinter import BasePrinter
from decoder.iso4909 import (cb_details, cl_details, cscn_details, format_code,
                             ic_details, pincp_details, rm_details, sr_details)

logger = logging.getLogger(__name__)


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
        matcher = re.match(r"^\;(?P<FC>[0-9]{2})(?P<MII>[0-9]{2})(?P<BLZ>[0-9]{8})\=(?P<KTO>[0-9]{10})(?P<CHK>[0-9]{1})\=(?P<CC>[0-9]{3})(?P<CuC>[0-9]{3})(?P<CE>[0-9]{1})(?P<AA>[0-9]{4})(?P<AR>[0-9]{4})(?P<CB>[0-9]{4})(?P<CL>[0-9]{2})(?P<RC>[0-9]{1})(?P<PINCP>[0-9]{6})(?P<IC>[0-9]{1})(?P<PANSR>[0-9]{2})(?P<FSANSR>[0-9]{2})(?P<SSANSR>[0-9]{2})(?P<ED>[0-9]{4})(?P<CSN>[0-9]{1})(?P<CScN>[0-9]{9}|\=)(?P<FSAN>[0-9]*|\=)(?P<SSAN>[0-9]*|\=)(?P<RM>[0-9]{1})(?P<CCD>[0-9]{6}|\=)(?P<AD>[^\?]*)\?$", data)
        if not matcher:
            logger.warn("Non-Girocard track 3 format: '%s'", data)
            return tuple(track_details)
        result = {
            "trackno": 3,  # inline signal track
            "FC": matcher.group("FC"),  # Format code
            "MII": matcher.group("MII"),  # MII, ISO 7812
            "BLZ": matcher.group("BLZ"),  # Routing code (Bankleitzahl)
            "KTO": matcher.group("KTO"),  # Account number (Kontonummer)
            # Routing and account number check digit (calculation depends on account holding institution)
            "CHK": matcher.group("CHK"),
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
            "CCD": matcher.group("CCD"),  # Crypto check digit
            "AD": matcher.group("AD"),  # Additional data
        }

        track_details[trackno - 1] = result
        return tuple(track_details)


class Printer(BasePrinter):
    def print_trackdata(self, track_details: tuple):
        for (trackno, data) in enumerate(track_details, 1):
            if trackno != 3:
                continue
            if data is None:
                print(f"No details for track {trackno}")
                continue

            print(f"Details for track {
                  trackno} =====================================")
            print(f"Format code:                    {data['FC']}")
            if self._print_verbose:
                print(
                    f"  ->                            {format_code(data['FC'])}")
            print(f"Major industry identifier:      {data['MII']}")
            if self._print_verbose and data['MII'] in iso7812.MII_DETAILS:
                print(
                    f"  ->                            {iso7812.MII_DETAILS[data['MII']]}")
            print(f"National routing number:        {data['BLZ']}")
            print(f"Account number:                 {data['KTO']}")
            print(f"Routing + acc check digit       {data['CHK']}")
            print(f"County code:                    {data['CC']}")
            print(f"Currency code:                  {data['CuC']}")
            print(f"Currency exponent:              {data['CE']}")
            print(f"Amount authorized (per cycle):  {data['AA']}")
            print(f"Amount remaining (this cycle):  {data['AR']}")
            print(f"Cycle begin (YDDD):             {data['CB']}")
            if self._print_verbose:
                print(
                    f"  ->                            {cb_details(data['CB'], data['ED'])}")
            print(f"Cycle length:                   {data['CL']}")
            if self._print_verbose:
                print(
                    f"  ->                            {cl_details(data['CL'])}")
            print(f"Retry count:                    {data['RC']}")
            print(f"PIN control parameters:         {data['PINCP']}")
            if self._print_verbose:
                print(
                    f"  ->                            {pincp_details(data['PINCP'], data['FC'])}")
            print(f"Interchange control:            {data['IC']}")
            if self._print_verbose:
                print(
                    f"  ->                            {ic_details(data['IC'])}")
            print(f"PAN service restiction:         {data['PANSR']}")
            if self._print_verbose:
                print(
                    f"  ->                            {sr_details(data['PANSR'])}")
            print(f"FSAN service restiction:        {data['FSANSR']}")
            if self._print_verbose:
                print(
                    f"  ->                            {sr_details(data['FSANSR'])}")
            print(f"SSAN service restiction:        {data['SSANSR']}")
            if self._print_verbose:
                print(
                    f"  ->                            {sr_details(data['SSANSR'])}")
            print(f"Expiry data (YYMM):             {data['ED']}")
            print(f"Card sequence number:           {data['CSN']}")
            print(f"Card security number:           {data['CScN']}")
            if self._print_verbose:
                print(
                    f"  ->                            {cscn_details(data['CScN'])}")
            print(f"First subsidiary accnt:         {data['FSAN']}")
            print(f"Second subsidiary accnt:        {data['SSAN']}")
            print(f"Relay marker:                   {data['RM']}")
            if self._print_verbose:
                print(
                    f"  ->                            {rm_details(data['RM'])}")
            print(f"Crypto check digits:            {data['CCD']}")
            print(f"Additional data (AD):           {data['AD']}")
