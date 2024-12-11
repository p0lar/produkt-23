import argparse
import logging
import sys

import decoder.raw.iso7813 as iso7813
import iso7812
import rawreader.datareader as datareader
from decoder import bahn, girocard, iso4909, noop
from decoder.plain import msr100
from rawreader import basereader, sigrok

logger = logging.getLogger()


def main():

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--input", choices=["msr100", "ardumsr", "sigrok_csv", "oneline"], default="msr100")
    ap.add_argument("--input-file", type=argparse.FileType("rt"),
                    help="A file containg the data for reading. Use '-' for stdin.")
    ap.add_argument("--input-track", choices=[1, 2, 3], default=2,
                    help="The input track to use to decode the raw input")
    ap.add_argument("--track1-processor", choices=[
                    "noop", "iso7813", "bahn"], default="noop", help="processor for track 1")
    ap.add_argument("--track2-processor", choices=[
                    "noop", "iso7813", "bahn"], default="noop", help="processor for track 2")
    ap.add_argument("--track3-processor", choices=[
                    "noop", "iso4909", "girocard", "bahn"], default="noop", help="processor for track 3")
    ap.add_argument("--remap-to-us", action="store_true",
                    default=False, help="Remap scancodes to US keyboard layout")
    ap.add_argument("--loop", action="store_true",
                    default=False, help="Loop reading cards")
    ap.add_argument("--print-verbose", action="store_true",
                    default=False, help="Print verbose track data")
    ap.add_argument("--log-level", choices=list(logging.getLevelNamesMapping().keys()),
                    default=logging.INFO, help="Print verbose track data")
    args = ap.parse_args()

    logging.basicConfig(level=logging.getLevelName(args.log_level))

    while True:

        bitstring = None
        trackdata = (None, None, None)  # The decoded data from the tracks
        error_reading = False

        try:
            if args.input == "oneline":
                rdr = datareader.FirstLine(args.input_file)
                bitstring = rdr.read_input()
            elif args.input == "sigrok_csv":
                rdr = sigrok.CsvReader(args.input_file)
                bitstring = rdr.read_input()
            elif args.input == "ardumsr":
                # The port the Arduino provides
                rdr = basereader.SerialReader(
                    port="/dev/ttyACM0", baudrate=9600)
                bitstring = rdr.read_input()
            elif args.input == "msr100":
                # No raw reader, decode directly
                rdr = msr100.Decoder(args.remap_to_us)
                trackdata = rdr.read_input()
            else:
                print(f"Unsupported input: {args.type}")
                error_reading = True
        except Exception as e:
            print(f"Error reading: {e}")
            error_reading = True
        finally:
            if error_reading:
                sys.exit(1)

        if bitstring is not None:
            dec = iso7813.Decoder(args.input_track)  # Decode as track n
            trackdata = dec.decode_bitstring(bitstring)
            print(f"Decoded track {args.input_track} data: '{trackdata[1]}'")
            # TODO: decode LRC here

        for (trackno, track) in enumerate(trackdata, 1):
            processor_choice = None
            trackdata_copy = ()
            if trackno == 1:
                processor_choice = args.track1_processor
                trackdata_copy = (track, None, None)
            elif trackno == 2:
                processor_choice = args.track2_processor
                trackdata_copy = (None, track, None)
            elif trackno == 3:
                processor_choice = args.track3_processor
                trackdata_copy = (None, None, track)
            else:
                print(f"Invalid trackno: {trackno}")

            parser = None
            printer = None

            if processor_choice == "noop":
                parser = noop.Parser()
                printer = noop.Printer()
            elif processor_choice == "iso7813":
                parser = iso7813.Parser()
                printer = iso7813.Printer(print_verbose=args.print_verbose)
            elif processor_choice == "iso4909":
                parser = iso4909.Parser()
                printer = iso4909.Printer(print_verbose=args.print_verbose)
            elif processor_choice == "bahn":
                parser = bahn.Parser()
                printer = bahn.Printer(print_verbose=args.print_verbose)
            elif processor_choice == "girocard":
                parser = girocard.Parser()
                printer = girocard.Printer(print_verbose=args.print_verbose)
            else:
                print(f"Unsupported processor for track {
                      trackno}: {processor_choice}")
                continue

            trackdata_details = parser.process_trackdata(trackdata_copy)
            if printer is not None:
                printer.print_trackdata(trackdata_details)

        if not args.loop:
            break


if __name__ == "__main__":
    main()
