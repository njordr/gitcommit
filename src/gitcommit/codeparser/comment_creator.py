import logging

from jinja2 import Environment, PackageLoader
from tempfile import NamedTemporaryFile
from typing import List


from gitcommit.codeparser.parsed_file import ParsedFile
from gitcommit.codeparser.commit import Commit


logger = logging.getLogger(__name__)


class CommentCreator:
    def __init__(
        self,
        parsed_files: List[ParsedFile],
        commit_obj: Commit,
        template_file: str = "standard.txt",
    ):
        self._env = Environment(
            loader=PackageLoader("gitcommit", "templates"), trim_blocks=True
        )
        self._template_file = template_file
        self._parsed_files = parsed_files
        self._temp_file = NamedTemporaryFile(delete=False, mode="w")
        self._commit = commit_obj

    @property
    def comment_file(self):
        return self._temp_file.name

    def run(self):
        try:
            template = self._env.get_template(self._template_file)
        except Exception as e:
            logger.error(f"Error loading template: {e}")
            raise

        try:
            rendered = template.render(
                commit=self._commit, parsed_files=self._parsed_files
            )
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            raise

        try:
            self._temp_file.write(rendered)
        except Exception as e:
            logger.error(f"Error writing rendered template to disk: {e}")
            raise

        self._temp_file.close()
