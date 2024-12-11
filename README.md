# produkt-23

Reviving a [magnetic card reader](https://www.kyubu.de/tech/magreader) from the 80's

# Dependencies

This project utilizes the keyboard modules for python:

    pip install keyboard

In case you modify the code for your own needs: Take care of the keyboard module usage. In no time you can have your keyboard disabled and won't get it back until next reboot.

# Data sources

The main script can read data from various sources:

* RAW data from a file (read bits on the first line) or stdin
* Sigrok csv data
* Cheap MSR-100 (or similar) 3-track magnetic card reader via USB. In case you've no US keyboard on site, a remapping from US keyboard scancodes exist to retrieve the correct data (Some cheap readers disregard the USB-HID scancodes).
* Arduino based magnetic card reader via serial port

# Decoding data

Some card data is decoded and printed on screen while reading:

* ISO-7813 Track 1 data
* ISO-7813 Track 2 data
* ISO-4909 Track 3 data
* German banking card data
* German rail card data
* Noop (Displays the raw data)

# Frontend usage

    usage: omron.py [-h]
                    [--input {msr100,ardumsr,sigrok_csv,oneline}]
                    [--input-file INPUT_FILE]
                    [--input-track {1,2,3}]
                    [--track1-processor {noop,iso7813,bahn}]
                    [--track2-processor {noop,iso7813,bahn}]
                    [--track3-processor {noop,iso4909,girocard,bahn}]
                    [--remap-to-us]
                    [--loop]
                    [--print-verbose]
                    [--log-level {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}]

    options:
      -h, --help            show this help message and exit
      --input {msr100,ardumsr,sigrok_csv,oneline}
      --input-file INPUT_FILE
                            A file containg the data for reading. Use '-' for stdin.
      --input-track {1,2,3}
                            The input track to use to decode the raw input
      --track1-processor {noop,iso7813,bahn}
                            processor for track 1
      --track2-processor {noop,iso7813,bahn}
                            processor for track 2
      --track3-processor {noop,iso4909,girocard,bahn}
                            processor for track 3
      --remap-to-us         Remap scancodes to US keyboard layout
      --loop                Loop reading cards
      --print-verbose       Print verbose track data
      --log-level {CRITICAL,FATAL,ERROR,WARN,WARNING,INFO,DEBUG,NOTSET}
                            Print verbose track data

# Arduino reader usage

Load the arduino code to the (Arduino) IDE and deploy it on your board.

Tested with an UNO R3 SMD. In case you want to use the frontend for reading, you need the serial interface configured accordingly.