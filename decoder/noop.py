from decoder.baseparser import BaseParser
from decoder.baseprinter import BasePrinter


class Printer(BasePrinter):

    def print_trackdata(self, track_details: tuple):
        for (trackno, data) in enumerate(track_details, 1):
            if data is None:
                continue
            print(f"Track {trackno} data: {data}")


class Parser(BaseParser):

    def process_trackdata(self, trackdata: tuple) -> tuple:
        return trackdata
