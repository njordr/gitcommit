import logging
import textwrap


logger = logging.getLogger(__name__)


class Commit:
    def __init__(self):
        self._summary = ''
        self._body = []

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, text: str):
        self._summary = text[:50]

    @property
    def body(self):
        return self._body

    @body.setter
    def body(self, text):
        self._body = textwrap.wrap(text)

