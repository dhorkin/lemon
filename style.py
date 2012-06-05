#! /usr/bin/env python

# Copyright (c) 2012 Victor Terron. All rights reserved.
# Institute of Astrophysics of Andalusia, IAA-CSIC
#
# This file is part of LEMON.
#
# LEMON is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import optparse
import textwrap

# Used to change the format with which the logging module displays messages
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Prefix that will be added to each line printed to the standard output
prefix = ">> "

# The error message to be printed if the execution is aborted.w
error_exit_message = "%sExecution aborted." % prefix

class NewlinesFormatter(optparse.IndentedHelpFormatter):
    """ This quick-and-dirty trick prevents optparse from stripping newlines
    (using textwrap) when the description of the module is printed. This should
    be acceptable enough until the transition to argparse is made. """

    def _format_text(self, text):
        text_width = self.width - self.current_indent
        indent = ' ' * self.current_indent
        # Wrap one paragraph at a time, then concatenate them
        formatted_text = ""
        for paragraph in text.split('\n\n'):

            formatted_text += textwrap.fill(paragraph.strip(),
                                            text_width,
                                            initial_indent=indent,
                                            subsequent_indent=indent)
            formatted_text += '\n\n'

        return formatted_text.rstrip()
