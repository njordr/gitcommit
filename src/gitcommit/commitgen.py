#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This is a skeleton file that can serve as a starting point for a Python
console script. To run this script uncomment the following lines in the
[options.entry_points] section in setup.cfg:

    console_scripts =
         fibonacci = gitcommit.skeleton:run

Then run `python setup.py install` which will install the command `fibonacci`
inside your current environment.
Besides console scripts, the header (i.e. until _logger...) of this file can
also be used as template for Python modules.

Note: This skeleton file can be safely removed if not needed!
"""

import sys
import logging
import click

from gitcommit import __version__

__author__ = "Giovanni Colapinto"
__copyright__ = "Giovanni Colapinto"
__license__ = "mit"

_logger = logging.getLogger(__name__)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(level=loglevel, stream=sys.stdout,
                        format=logformat, datefmt="%Y-%m-%d %H:%M:%S")


@click.command()
@click.argument('path')
@click.argument('loglevel')
def main(path: str, loglevel: str):
    """Main entry point allowing external calls

    Args:
      str ([str]): base path for code to inspect
      loglevel: log level
    """
    setup_logging(loglevel)
    _logger.debug("Starting crazy calculations...")
    _logger.info("Script ends here")
