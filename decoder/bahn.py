import logging
import re
from datetime import datetime

from decoder.baseparser import BaseParser
from decoder.baseprinter import BasePrinter
from decoder.utils import check_luhn

logger = logging.getLogger(__name__)


class Printer(BasePrinter):
    def print_trackdata(self, track_details: tuple):
        for (trackno, data) in enumerate(track_details, 1):
            if trackno == 3:
                break
            if data is None:
                print(f"No details for track {trackno}")
                continue

            print(f"Details for track {
                  trackno} =====================================")
            if trackno == 1:
                print(f"Bahncard number: {
                      data['BCNR']} (valid: {check_luhn(data['BCNR'])})")
                print(f"Valid from:  {
                      datetime.strptime(data['VS'], '%Y%m%d')}")
                print(f"Valid until: {
                      datetime.strptime(data['VE'], '%Y%m%d')}")
                print(f"Marker:      {data['MARK']}")
                print(f"Additional:  {data['AD']}")
            elif trackno == 2:
                print(f"Bahncard number: {
                      data['BCNR']} (valid: {check_luhn(data['BCNR'])})")
                print(f"Valid from:  {
                      datetime.strptime(data['VS'], '%Y%m%d')}")
                print(f"Valid until: {
                      datetime.strptime(data['VE'], '%Y%m%d')}")


class Parser(BaseParser):
    def process_trackdata(self, trackdata: tuple) -> tuple:
        track_details = [None, None, None]
        for (trackno, data) in enumerate(trackdata, 1):
            if data is None:
                print(f"No details for track {trackno}")
                continue
            if trackno == 1:
                matcher = re.match(
                    r"^%(?P<FC>[A-Z])(?P<BCNR>[0-9]{1,19})\^(?P<VS>[0-9]{8})\^(?P<VE>[0-9]{8})\^(?P<MARK>[^\^]{1,})\^(?P<AD>[^\?]*)\?$", data)
                if not matcher:
                    logger.warn("Non-Bahncard track 1 format: '%s'", data)
                    continue
                result = {
                    "trackno": trackno,  # inline signal track
                    "FC": matcher.group("FC"),  # Format code
                    "BCNR": matcher.group("BCNR"),  # Bahncard numner
                    "VS": matcher.group("VS"),  # Valid start
                    "VE": matcher.group("VE"),  # Valid end
                    # Marker HK Hauptkarte, PK Partnerkarte
                    "MARK": matcher.group("MARK"),
                    "AD": matcher.group("AD"),  # Additional data
                }
            elif trackno == 2:
                matcher = re.match(
                    r"^\;(?P<BCNR>[0-9]{1,19})\=(?P<VS>[0-9]{8})\=(?P<VE>[0-9]{8})(?P<AD>[^\?]*)\?$", data)
                if not matcher:
                    logger.warn("Non-Bahncard track 2 format: '%s'", data)
                    return tuple(track_details)
                result = {
                    "trackno": trackno,  # inline signal track
                    "BCNR": matcher.group("BCNR"),  # Bahncard numner
                    "VS": matcher.group("VS"),  # Valid start
                    "VE": matcher.group("VE"),  # Valid end
                }
            logger.debug("Bahncard track %d data: %s", trackno, data)
            track_details[trackno - 1] = result
        return tuple(track_details)
