import logging
import re
import tempfile
import shutil
import os

from git import Repo
from huepy import *
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
        remove_comments: bool = False,
        untracked: bool = False,
        backup_dir: str = None
    ):
        self._path = path
        self._mark = f"{comment}{mark}"
        self._re = re.compile(f".*{self._mark}.*")
        self._changed_files = []
        self._commented_files = []
        self._uncommented_files = []
        self._new_files = []
        self._parsed_files = []
        self._remove_comments = remove_comments
        self._untracked = untracked
        self._summary = summary
        self._body = body
        self._commit = None
        self._temp_dir = tempfile.mkdtemp()
        if backup_dir is None:
            self._backup_dir = tempfile.mkdtemp()
        else:
            self._backup_dir = backup_dir

    def run(self):
        self._commit = Commit()
        self._commit.summary = self._summary
        self._commit.body = self._body
        self._get_git_changes()
        self._parse_changed_files()

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

        commit_file = ''
        with open(creator.comment_file, 'r') as f:
            commit_file = f.read()

        print(lightgreen(f"This is the content of your git commit message:"))
        print('------------------------------------------------')
        print(commit_file)
        print('------------------------------------------------')
        print(lightgreen(f'You can find it here: {creator.comment_file}'))

        if self._remove_comments:
            choose = input(lightred("Are you sure you want to remove gitcommit comments from code? [y/N]"))
            if choose == 'y':
                self._remove_comments_from_code()
                print(lightgreen(f"gitcommit comments removed from codebase"))
            else:
                print(orange(f"gitcommit comments NOT removed from codebase"))
                print(orange(f"Review code changes at {self._temp_dir}"))
        else:
            print(orange(f"Review code changes at {self._temp_dir}"))

        if self._uncommented_files:
            print(lightred(f"\nThe following files have code changes but no gitcomment marks"))
            for file_name in self._uncommented_files:
                print(file_name)

        print(lightblue(f'\nUse it in git with \n"git commit -f {creator.comment_file}"'))

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
                self._changed_files.append(entry)

    def _parse_changed_files(self):
        for code_file in self._changed_files:
            parsed = ParsedFile(file_name=code_file)
            line_nr = 1
            new_file = []
            commented = False
            with open(f"{self._path}/{code_file}", "r") as f:
                for line in f:
                    try:
                        new_line, line_commented = self._parse_line(
                            line=line, line_nr=line_nr, parsed_obj=parsed
                        )
                        if not line_commented:
                            new_file.append(new_line)
                        else:
                            if new_line.strip() != "":
                                new_file.append(new_line)

                        if not commented and line_commented:
                            commented = True
                    except Exception as e:
                        logger.error(f"Error parsing line {line}; {e}")

                    line_nr += 1

            if not commented:
                self._uncommented_files.append(code_file)

            self._parsed_files.append(parsed)
            self._write_intermediate_file(
                commented=commented, file_name=code_file, file_content=new_file
            )

    def _write_intermediate_file(self, commented: bool, file_name: str, file_content: list):
        if not commented:
            logger.debug(f"File {file_name} skipped because no gitcomment comments in it")
            return

        directories = file_name.split(os.sep)[:-1]
        if directories:
            directories = os.path.join(*directories)
            try:
                os.makedirs(os.path.join(self._temp_dir, directories), exist_ok=True)
            except Exception as e:
                logger.error(f"Error creating directories {directories}: {e}")
                raise

        file_abs_path = os.path.join(self._temp_dir, file_name)

        try:
            with open(file_abs_path, "w") as f:
                f.write("".join(file_content))
        except Exception as e:
            logger.error("Error writing intermediate file {file_name}: {e}")
            raise

        self._commented_files.append(file_name)

    def _remove_comments_from_code(self):
        for file_name in self._commented_files:
            src = os.path.join(self._temp_dir, file_name)
            dst = os.path.join(self._path, file_name)
            logger.debug(f"Copy file {src} to {dst}")
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                logger.error(f"Error copying {src} to {dst}: {e}")
                continue

        try:
            shutil.rmtree(self._temp_dir, ignore_errors=True)
        except Exception as e:
            logger.error(f"Error deleting tmp dir: {e}")
            logger.error((f"Please delete dir {self._temp_dir} by yourself"))

    def _parse_line(self, line: str, line_nr: int, parsed_obj: ParsedFile) -> str:
        commented = False
        if not self._re.search(line):
            logger.debug(f"Line |{line.strip()}| skipped because no regex matches")
            return line, commented

        logger.debug(f"Line |{line.strip()}| matches regex")
        commented = True
        chunks = line.split(self._mark)
        new_line = chunks[0]

        if new_line == "":
            # comment line, need to add 1 to line_nr because it refers to the following line
            line_nr += 1

        parsed_obj.add_comment(
            comment=chunks[1].replace(self._mark, "").strip(), line_nr=line_nr
        )

        new_line += '\n'

        return new_line, commented
