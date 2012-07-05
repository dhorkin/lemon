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

""" Definition of the default options used by the different modules """

import multiprocessing

desc = {} # option descriptions (for optparse)

ncores = multiprocessing.cpu_count()
desc['ncores'] = \
"the maximum number of cores available to the module. This option " \
"defaults to the number of CPUs in the system, which are automatically " \
"detected [default: %default]"

maximum = 50000
desc['maximum'] = \
"the CCD saturation level, in ADUs. Those star which have one or more " \
"pixels above this value are considered to be saturated. Note that, for " \
"coadded images, the effective saturation level is obtained by multiplying " \
"this value by the number of coadds (see --coaddk option) [default: %default]"

margin = 250
desc['margin'] = \
"the width, in pixels, of the areas adjacent to the edges that will be " \
"ignored when detecting sources on the reference image. Stars whose center " \
"is fewer than 'margin' pixels from any border (horizontal or vertical) of " \
"the FITS image are not considered. [default: %default]"
