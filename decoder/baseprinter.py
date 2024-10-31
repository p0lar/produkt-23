class BasePrinter:

    _print_verbose = False

    def __init__(self, print_verbose=False) -> None:
        self._print_verbose = print_verbose

    """Prints the decoded tuple"""

    def print_trackdata(self, track_details: tuple) -> tuple:
        raise ("Not implemented!")
