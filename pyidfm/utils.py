from io import StringIO
from html.parser import HTMLParser

from pyidfm.types import LineId, ShortLineId

# from https://stackoverflow.com/questions/753052/strip-html-from-strings-in-python


class MLStripper(HTMLParser):
    """
    Class used to remove HTML tags from a string
    """

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, d: str) -> None:
        self.text.write(d)

    def get_data(self) -> str:
        return self.text.getvalue()


def strip_html(html: str) -> str:
    """
    Removes HTML tags from the specified string

    :param html: the string that contains the HTML tags to remove
    :return: The specified string without the HTML tags
    """
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def to_short_line_id(line_id: LineId) -> ShortLineId:
    """
    Converts a line ID from the format "STIF:Line::XXX:" to the format "CXXX"

    :param line_id: the line ID to convert
    :return: the converted line ID
    """
    return line_id.split(":")[-2]
