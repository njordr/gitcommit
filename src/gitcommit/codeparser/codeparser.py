import logging
import re

from git import Repo
from pprint import pprint

from gitcommit.codeparser.parsed_file import ParsedFile
from gitcommit.codeparser.comment_creator import CommentCreator
from gitcommit.codeparser.commit import Commit


logger = logging.getLogger(__name__)


class CodeParser:
    def __init__(
        self,
        path: str,
        summary: str,
        body: str = "",
        comment: str = "#",
        mark: str = "->",
        dry_run: bool = False,
        untracked: bool = False,
        debug: bool = False,
    ):
        self._path = path
        self._mark = f"{comment}{mark}"
        self._re = re.compile(f".*{self._mark}.*")
        self._changed_files = []
        self._new_files = []
        self._parsed_files = []
        self._dry_run = dry_run
        self._untracked = untracked
        self._debug = debug
        self._debug_ext = "gitcommit"
        self._summary = summary
        self._body = body
        self._commit = None

    def run(self):
        logger.info("Start code parser")
        self._commit = Commit()
        self._commit.summary = self._summary
        self._commit.body = self._body
        self._get_git_changes()
        self._parse_changed_files()
        if self._untracked:
            self._parse_new_files()

        try:
            creator = CommentCreator(
                parsed_files=self._parsed_files, commit_obj=self._commit
            )
        except Exception as e:
            logger.error(f'Error creating CommentCreator class: {e}')
            raise

        try:
            creator.run()
        except Exception as e:
            logger.error(f"Error running CommentCreator: {e}")
            raise

        return creator.comment_file

    def _get_git_changes(self):
        try:
            repo = Repo(self._path)
        except Exception as e:
            logger.error(f"Error creating Repo class; {e}")
            raise

        if repo is None:
            raise RuntimeError(f"Cannot open git repository at {self._path}")

        index = repo.index
        for entry in index.diff(None):
            self._changed_files.append(entry.a_path)

        if self._untracked:
            for entry in repo.untracked_files:
                self._new_files.append(entry)

    def _parse_changed_files(self):
        for code_file in self._changed_files:
            if code_file.endswith(self._debug_ext):
                pprint(code_file)
                continue
            parsed = ParsedFile(file_name=code_file)
            line_nr = 1
            new_file = []
            changed = False
            with open(f"{self._path}/{code_file}", "r") as f:
                for line in f:
                    try:
                        new_line, changed = self._parse_line(
                            line=line, line_nr=line_nr, parsed_obj=parsed
                        )
                        if not changed:
                            new_file.append(new_line)
                        else:
                            if new_line.strip() != "":
                                new_file.append(new_line)
                    except Exception as e:
                        logger.error(f"Error parsing line {line}; {e}")

                    line_nr += 1

            self._parsed_files.append(parsed)
            self._write_clean_file(
                changed=changed, file_name=code_file, file_content=new_file
            )

    def _parse_new_files(self):
        for code_file in self._new_files:
            line_nr = 1
            new_file = []
            changed = False
            with open(f"{self._path}/{code_file}", "r") as f:
                for line in f:
                    try:
                        new_line, changed = self._parse_line(
                            line=line, line_nr=line_nr, file_name=code_file
                        )
                        if not changed:
                            new_file.append(new_line)
                        else:
                            if new_line.strip() != "":
                                new_file.append(new_line)
                    except Exception as e:
                        logger.error(f"Error parsing line {line}; {e}")

                    line_nr += 1

            self._write_clean_file(
                changed=changed, file_name=code_file, file_content=new_file
            )

    def _write_clean_file(self, changed: bool, file_name: str, file_content: list):
        file_name = f"{self._path}/{file_name}"
        if self._debug:
            file_name = f"{file_name}.{self._debug_ext}"

        if not self._dry_run and changed:
            with open(file_name, "w") as f:
                f.write("".join(file_content))
        elif self._debug and changed:
            with open(file_name, "w") as f:
                f.write("".join(file_content))

    def _parse_line(self, line: str, line_nr: int, parsed_obj: ParsedFile) -> str:
        changed = False
        if not self._re.search(line):
            return line, changed

        changed = True
        chunks = line.split(self._mark)
        new_line = chunks[0]

        if new_line == "":
            # comment line, need to add 1 to line_nr because it refers to the following line
            line_nr += 1

        parsed_obj.add_comment(
            comment=chunks[1].replace(self._mark, "").strip(), line_nr=line_nr
        )

        return new_line, changed
