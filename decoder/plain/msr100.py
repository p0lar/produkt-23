import logging
import sys
import keyboard
from .. basedecoder import BaseDecoder
from .. raw.iso7813 import sentinels, SS

from decoder.plain import remap

logger = logging.getLogger(__name__)

# ALiases for list indices
TRACK_1 = 0
TRACK_2 = 1
TRACK_3 = 2


class Decoder(BaseDecoder):

    _remap_from_us = False

    def __init__(self, remap_from_us: bool = False) -> None:
        super().__init__()
        self._remap_from_us = remap_from_us

    def _build_result(self, key_events: list) -> list:
        logger.debug("Reader input took %d seconds, %d keystrokes",
                     key_events[-1].time - key_events[0].time, len(key_events))
        data_read = []
        b = None
        buf = ""
        for e in key_events:
            map_name = ""
            if e.event_type == keyboard.KEY_UP or (e.event_type == keyboard.KEY_DOWN and "shift" in e.name):
                b = e
                continue
            if e.event_type == keyboard.KEY_DOWN and b is not None and b.event_type == keyboard.KEY_DOWN and "shift" in b.name:
                # Shift pressed before key
                map_name = f"shift-{e.scan_code}"
            else:
                map_name = f"{e.scan_code}"
            b = e
            if e.name == "enter":  # New line
                if len(buf) > 0:
                    data_read.append(buf)
                    logger.debug("read buffer: '%s'", buf)
                buf = ""
                continue
            if self._remap_from_us:
                buf += remap.US_PS2[map_name]
            elif e.name == "space":
                buf += " "
            else:
                buf += e.name
        return data_read

    def flush_input(self):
        try:
            # Flush on windows
            import msvcrt
            while msvcrt.kbhit():
                msvcrt.getch()
        except ImportError:
            # Flush on unix
            import termios
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)

    def read_input(self) -> tuple:
        # The reader returns up to 3 tracks, separated by \n, ordered from track 1 to track 3.
        # If a track yields no data, no line is returned. If all tracks are read, a
        # single \n is isssued.
        result = [None, None, None]
        len_read = -1
        data_in_end = False
        data_end_hotkey = "enter, enter"
        key_events = []
        print(f"Waiting for data, press '{data_end_hotkey}' to exit ...")
        try:
            while not data_in_end:
                # Use keyboard for capturing the scancodes
                key_events = keyboard.record(data_end_hotkey, suppress=True)
                len_read = len(key_events)
                if len_read > 0:
                    data_in_end = True
        finally:
            self.flush_input()  # Flush the keyboard input buffer that was filled during record

        data_read = self._build_result(key_events=key_events)

        if len(data_read) == 3:  # All tracks have data, we're done
            logger.debug("3 track read")
            result = (data_read[0], data_read[1], data_read[2])

        elif len(data_read) == 2:  # Do some guesswork based on iso7813
            logger.debug("2 tracks read")
            # This could be:
            # * track 1 + track 2
            # * track 1 + track 3
            # * track 2 + track 3
            start_sentinels = (data_read[0][0], data_read[1][0])
            if start_sentinels[0] == sentinels[2][SS]:  # This can only be track 2 + 3
                result[TRACK_2] = data_read[0]
                result[TRACK_3] = data_read[1]
            # This is track 1 + 3, since track 2 only contains 40 symbols max
            elif len(data_read[1]) > 40:
                result[TRACK_1] = data_read[0]
                result[TRACK_3] = data_read[1]
            else:  # track 1 + 2
                result[TRACK_1] = data_read[0]
                result[TRACK_2] = data_read[1]

        elif len(data_read) == 1:  # Do some guesswork based on iso7813
            logger.debug("1 track read")
            start_sentinel = data_read[0][0]
            data_len = len(data_read[0])
            if (start_sentinel == sentinels[3][SS]) and data_len > 40:
                # track 3 (iso 4909)
                result[TRACK_3] = data_read[0]
            elif start_sentinel == sentinels[2][SS]:
                # track 2 (iso 7813)
                result[TRACK_2] = data_read[0]
            elif start_sentinel == sentinels[1][SS] and data_len > 40:
                # track 1 (iso 7813)
                result[TRACK_1] = data_read[0]
            else:
                result[TRACK_3] = data_read[0]

        return tuple(result)
