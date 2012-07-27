#! /usr/bin/env python
# encoding:UTF-8

# Copyright (c) 2012 Victor Terron. All rights reserved.
# Institute of Astrophysics of Andalusia, IAA-CSIC
#
# This file is part of LEMON.
#
# LEMON is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from __future__ import division

import datetime
import pygtk
pygtk.require ('2.0')
import gtk
import os.path
import sys

# http://stackoverflow.com/a/1054293/184363
path = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.append(path)

# LEMON modules
import database
import glade
import methods
import util

class LEMONJuicerGUI(object):

    def __init__ (self, *args, **kwds):
        super(LEMONJuicerGUI, self).__init__(*args, **kwds)

        builder = gtk.Builder()
        builder.add_from_file(glade.GUI_MAIN)
        builder.connect_signals(self)

        self._main_window = builder.get_object('main-window')
        self._notebook    = builder.get_object('main-notebook')
        self._box_toolbar = builder.get_object('box-toolbar')
        self._status_bar  = builder.get_object('status-bar')

        self._main_window.show()
        self._builder = builder

        self.db = None  # instance of the LEMONdB class

    def run(self):
        gtk.main()

    def handle_close(self, obj):
        self._main_window.destroy()

    def handle_show_about(self, obj):
        self._builder.add_from_file(glade.GUI_ABOUT)
        about = self._builder.get_object('about-dialog')
        about.set_transient_for(self._main_window)
        about.run()
        about.destroy()

    def handle_destroy(self, win):
        gtk.main_quit()

    def handle_toggle_view_sexagesimal(self, *args):
        button = self._builder.get_object('radio-view-sexagesimal')
        active = button.get_active()
        try:
            self.view.get_column( self.ra_sex_index).set_visible(active)
            self.view.get_column(self.dec_sex_index).set_visible(active)
        # Raised if no LEMONdB has yet been loaded
        except AttributeError:
            pass

    def handle_toggle_view_decimal(self, *args):
        button = self._builder.get_object('radio-view-decimal')
        active = button.get_active()
        try:
            self.view.get_column( self.ra_dec_index).set_visible(active)
            self.view.get_column(self.dec_dec_index).set_visible(active)
        except AttributeError:
            pass

    def handle_select_period_units(self, button):

        def set_column(index):
            """ Set the visibility of the index-th column of the GtkTreeView,
            depending on whether the button is active or not"""
            self.view.get_column(index).set_visible(button.get_active())

        try:
            if button.get_label() == 'Days':
                for index in self.period_days_indexes:
                    set_column(index)

            elif button.get_label() == 'hh:mm:ss':
                for index in self.period_hhmmss_indexes:
                    set_column(index)

            elif button.get_label() == 'Seconds':
                for index in self.period_seconds_indexes:
                    set_column(index)
            else:
                msg = "unknown button label"
                raise ValueError(msg)

        except AttributeError:
            pass

    def handle_open(self, window):
        kwargs = dict(title = None,
                      action = gtk.FILE_CHOOSER_ACTION_OPEN,
                      buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                 gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        with util.destroying(gtk.FileChooserDialog(**kwargs)) as dialog:

            filt = gtk.FileFilter()
            pattern = '*.LEMONdB'
            filt.set_name('LEMON Database (%s)' % pattern)
            filt.add_mime_type('application/octet-stream; charset=binary')
            filt.add_pattern(pattern)
            dialog.add_filter(filt)

            response = dialog.run()
            if response == gtk.RESPONSE_OK:
                path = dialog.get_filename()
                dialog.destroy()
                self.open_db(path)

    def open_db(self, path):

        # If this is not the first LEMONdB that is opened, warn the user that
        # the current one will be closed, unless the operation is aborted.
        if self.db is not None:
            title = "Are you done with this database?"
            msg = ("Unfortunately, data analysis must be done on one LEMONdB "
                   "at a time, so opening a new one will close all your "
                   "current tabs. Do you really want to proceed?")
            args = self._main_window, title, msg
            kwargs = dict(msg_type = gtk.MESSAGE_QUESTION,
                          buttons = gtk.BUTTONS_OK_CANCEL)
            response = util.show_message_dialog(*args, **kwargs)

            # If the user presses OK, close all the tabs of the notebook.
            # Otherwise, the load is cancelled and nothing is modified.
            if response == gtk.RESPONSE_OK:
                while self._notebook.get_n_pages():
                    self._notebook.remove_page(-1)
            else:
                return

        self._builder.add_from_file(glade.GUI_OVERVIEW)
        overview = self._builder.get_object('database-overview')
        self.view = self._builder.get_object('table-view')

        # Display a dialog with a progress bar which is updated as all the
        # stars are loaded into memory, as this may take a while. A 'Cancel'
        # button allows the process to be interrupted at any time.
        self._builder.add_from_file(glade.LOADING_DIALOG)
        dialog = self._builder.get_object('loading-dialog')
        dialog.set_transient_for(self._main_window)
        progressbar = self._builder.get_object('loading-progressbar')

        self._aborted = False
        def cancel(*args):
            self._aborted = True
        dialog.connect('response', cancel)
        dialog.show()

        try:

            db = database.LEMONdB(path)
            db_pfilters = db.pfilters

            # Two columns are used for the right ascension and declination of
            # the stars, with the sexagesimal and decimal coordinates. They
            # will be shown depending on the radio button selected at View -
            # Coordinates, but the decimal coordinates are always needed, as
            # sexagesimal ones are sorted by them, not lexicographically.

            star_attrs = ['ID', 'α', 'α', 'δ', 'δ', 'm']

            assert star_attrs.count('α') == 2
            assert star_attrs.count('δ') == 2
            self.ra_sex_index = star_attrs.index('α')
            self.ra_dec_index = self.ra_sex_index + 1
            self.dec_sex_index = star_attrs.index('δ')
            self.dec_dec_index = self.dec_sex_index + 1

            # Three columns are used for each period, to show it in days (a
            # real number), hh:mm:ss (str) or seconds (int). Periods will be
            # sorted always by their value in seconds. We need to keep an
            # internal list with the indexes of each type of column, to make
            # them visible or not depending on the option selected at View -
            # Periods.

            self.period_days_indexes = []
            self.period_hhmmss_indexes = []
            self.period_seconds_indexes = []

            for pfilter in db_pfilters:
                label = "Period %s" % pfilter.letter
                star_attrs += [label] * 3
                length = len(star_attrs)
                self.period_days_indexes.append(length - 3)
                self.period_hhmmss_indexes.append(length - 2)
                self.period_seconds_indexes.append(length - 1)

            args = [float, str, int] * len(db.pfilters)
            self.store = gtk.ListStore(int, str, float, str, float, float, *args)

            for index, attribute in enumerate(star_attrs):
                render = gtk.CellRendererText()
                column = gtk.TreeViewColumn(attribute, render, text = index)
                column.props.resizable = False

                # Set the current sort comparison function of the column
                if index == self.ra_sex_index:
                    sort_index = self.ra_dec_index
                elif index == self.dec_sex_index:
                    sort_index = self.dec_dec_index

                # Periods are in the following order: days, hh:mm:ss, seconds.
                # We want to sort hh:mm:ss periods not lexicographically, but
                # by the value of the third column, which stores seconds.
                elif index in self.period_hhmmss_indexes:
                    sort_index = index + 1
                else:
                    sort_index = index
                column.set_sort_column_id(sort_index)

                self.view.append_column(column)

            nstars = len(db)
            for star_index, star_id in enumerate(db.star_ids):

                # Has the user pressed 'Cancel'?
                if self._aborted:
                    break

                x, y, ra, dec, imag = db.get_star(star_id)
                ra_str  = methods.ra_str(ra)
                dec_str = methods.dec_str(dec)
                row = [star_id, ra_str, ra, dec_str, dec, imag]

                for pfilter in db_pfilters:
                    # Returns a two-element tuple, with the period of the star,
                    # in seconds, and the step that the string-length method
                    # used. In case the period is unknown, None is returned.
                    star_period = db.get_period(star_id, pfilter)
                    if star_period is None:
                        # Use -1 for unknown values
                        row += [-1, '-1', -1]
                    else:
                        period, step = star_period
                        row.append(period / 3600 / 24) # hours
                        row.append(str(datetime.timedelta(seconds = period)))
                        row.append(period) # seconds

                self.store.append(row)

                fraction = star_index / nstars
                progressbar.set_fraction(fraction)
                # Ensure the progress bar is immediately rendered
                while gtk.events_pending():
                    gtk.main_iteration()

            if not self._aborted:

                # Save the LEMONdB for later use now that the load has been
                # completed; we could not do it earlier as it could have been
                # aborted
                self.db = db

                # Show sexagesimal, decimal coordinates or both
                self.handle_toggle_view_sexagesimal()
                self.handle_toggle_view_decimal()

                # Hide all the period columns but one
                buttons = [self._builder.get_object('radio-view-period-days'),
                           self._builder.get_object('radio-view-period-hhmmss'),
                           self._builder.get_object('radio-view-period-seconds')]
                for button in buttons:
                    self.handle_select_period_units(button)


                label = gtk.Label(os.path.basename(path))
                self._notebook.append_page(overview, label)
                self._notebook.set_tab_reorderable(overview, False)
                self._notebook.set_current_page(-1)

                self.view.set_model(self.store)

                title = 'Success'
                msg = "%s stars loaded" % nstars
                util.show_message_dialog(self._main_window, title, msg)

        except Exception, err:
            path = os.path.basename(path)
            title = "Error while loading LEMON database"
            msg = "File '%s' could not be loaded: %s" % (path, str(err))
            util.show_error_dialog(self._main_window, title, msg)

        finally:
            dialog.destroy()