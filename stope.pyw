#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright or © or Copr. Thomas Duchesne <thomas@duchesne.io>, 2014-2015
# 
# This software was funded by the Van Allen Foundation <http://fondation-va.fr>.
# 
# This software is governed by the CeCILL license under French law and
# abiding by the rules of distribution of free software.  You can  use, 
# modify and/ or redistribute the software under the terms of the CeCILL
# license as circulated by CEA, CNRS and INRIA at the following URL
# "http://www.cecill.info". 
# 
# As a counterpart to the access to the source code and  rights to copy,
# modify and redistribute granted by the license, users are provided only
# with a limited warranty  and the software's author,  the holder of the
# economic rights,  and the successive licensors  have only  limited
# liability. 
# 
# In this respect, the user's attention is drawn to the risks associated
# with loading,  using,  modifying and/or developing or reproducing the
# software by the user in light of its specific status of free software,
# that may mean  that it is complicated to manipulate,  and  that  also
# therefore means  that it is reserved for developers  and  experienced
# professionals having in-depth computer knowledge. Users are therefore
# encouraged to load and test the software's suitability as regards their
# requirements in conditions enabling the security of their systems and/or 
# data to be ensured and,  more generally, to use and operate it in the 
# same conditions as regards security. 
# 
# The fact that you are presently reading this means that you have had
# knowledge of the CeCILL license and that you accept its terms.

"""Main file of STOPE.

Catches the command line arguments and then choses the right interface to start
and sets the minimal logging level.

..seealso:: :mod:`gui`
"""

import argparse
import logging

import log
import gui

cli_parser = argparse.ArgumentParser(prog="stope", description="Simple Tool for Orbital Paremeter Extraction")
cli_parser.add_argument("--debug", help="Enable debug mode", action="store_true")
cli_parser.add_argument("--version", action="version", version="1.0")
cli_arguments = cli_parser.parse_args()

logger = logging.getLogger("root")
logger.info("STOPE is starting!")

if cli_arguments.debug:
    log.log_events(level=logging.DEBUG)
    logger.info("Debug mode enabled.")
else:
    log.log_events(level=logging.INFO)

gui.start()
