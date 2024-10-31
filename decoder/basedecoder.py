class BaseDecoder:
    """Class for decoding the input and return the result in a
    tuple of 3. The tuple represents the decoded data from all
    three tracks, first element is track 1, etc. If no data was read
    from a card's track the tuple's element is None.
    """

    def read_input(self) -> tuple:
        raise ("Not yet implemented!")
