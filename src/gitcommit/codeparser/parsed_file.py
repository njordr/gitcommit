import logging


logger = logging.getLogger(__name__)


class ParsedFile:
    def __init__(self, file_name: str, tracked: bool = True):
        self._file_name = file_name
        self._comments = []
        self._tracked = tracked

    @property
    def comments(self):
        return self._comments

    @property
    def tracked(self):
        return self._tracked

    @property
    def file_name(self):
        return self._file_name

    def add_comment(self, comment: str, line_nr: str):
        self._comments.append({"comment": comment, "line_nr": line_nr})

