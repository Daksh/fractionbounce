# -*- coding: utf-8 -*-
#Copyright (c) 2011, Walter Bender, Paulina Clares, Chris Rowe

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

import gtk

from sugar.activity import activity
try:  # 0.86+ toolbar widgets
    from sugar.graphics.toolbarbox import ToolbarBox
    HAS_TOOLBARBOX = True
except ImportError:
    HAS_TOOLBARBOX = False
if HAS_TOOLBARBOX:
    from sugar.graphics.toolbarbox import ToolbarButton
    from sugar.activity.widgets import ActivityToolbarButton
    from sugar.activity.widgets import StopButton
from sugar.graphics.radiotoolbutton import RadioToolButton
from sugar.graphics.toolbutton import ToolButton

from gettext import gettext as _

import logging
_logger = logging.getLogger('fractionbounce-activity')

from bounce import Bounce


def _entry_factory(default_string, toolbar, tooltip='', max=3):
    """ Factory for adding a text box to a toolbar """
    entry = gtk.Entry()
    entry.set_text(default_string)
    if hasattr(entry, 'set_tooltip_text'):
        entry.set_tooltip_text(tooltip)
    entry.set_width_chars(max)
    entry.show()
    toolitem = gtk.ToolItem()
    toolitem.add(entry)
    toolbar.insert(toolitem, -1)
    toolitem.show()
    return entry


def _button_factory(icon_name, toolbar, callback, cb_arg=None, tooltip=None,
                    accelerator=None):
    """Factory for making toolbar buttons"""
    button = ToolButton(icon_name)
    button.set_tooltip(tooltip)
    button.props.sensitive = True
    if accelerator is not None:
        button.props.accelerator = accelerator
    if cb_arg is not None:
        button.connect('clicked', callback, cb_arg)
    else:
        button.connect('clicked', callback)
    if hasattr(toolbar, 'insert'):  # the main toolbar
        toolbar.insert(button, -1)
    else:  # or a secondary toolbar
        toolbar.props.page.insert(button, -1)
    button.show()
    return button


def _radio_factory(button_name, toolbar, callback, cb_arg=None, tooltip=None,
                   group=None):
    ''' Add a radio button to a toolbar '''
    button = RadioToolButton(group=group)
    button.set_named_icon(button_name)
    if callback is not None:
        if cb_arg is None:
            button.connect('clicked', callback)
        else:
            button.connect('clicked', callback, cb_arg)
    if hasattr(toolbar, 'insert'):  # Add button to the main toolbar...
        toolbar.insert(button, -1)
    else:  # ...or a secondary toolbar.
        toolbar.props.page.insert(button, -1)
    button.show()
    if tooltip is not None:
        button.set_tooltip(tooltip)
    return button


def _label_factory(toolbar, label_text, width=None):
    ''' Factory for adding a label to a toolbar '''
    label = gtk.Label(label_text)
    label.set_line_wrap(True)
    if width is not None:
        label.set_size_request(width, -1)  # doesn't work on XOs
    label.show()
    _toolitem = gtk.ToolItem()
    _toolitem.add(label)
    toolbar.insert(_toolitem, -1)
    _toolitem.show()
    return label


def _separator_factory(toolbar, expand=False, visible=True):
    ''' add a separator to a toolbar '''
    _separator = gtk.SeparatorToolItem()
    _separator.props.draw = visible
    _separator.set_expand(expand)
    toolbar.insert(_separator, -1)
    _separator.show()


class FractionBounceActivity(activity.Activity):

    def __init__(self, handle):
        ''' Initiate activity. '''
        super(FractionBounceActivity, self).__init__(handle)

        self.add_events(gtk.gdk.VISIBILITY_NOTIFY_MASK)
        self.connect('visibility-notify-event', self.__visibility_notify_cb)

        # no sharing
        self.max_participants = 1

        custom_toolbar = gtk.Toolbar()
        if HAS_TOOLBARBOX:
            toolbox = ToolbarBox()

            activity_button = ActivityToolbarButton(self)
            toolbox.toolbar.insert(activity_button, 0)
            activity_button.show()

            custom_toolbar_button = ToolbarButton(
                label=_('Custom'),
                page=custom_toolbar,
                icon_name='view-source')
            custom_toolbar.show()
            toolbox.toolbar.insert(custom_toolbar_button, -1)
            custom_toolbar_button.show()

            self._load_standard_buttons(toolbox.toolbar)

            _separator_factory(toolbox.toolbar, expand=True, visible=False)

            stop_button = StopButton(self)
            stop_button.props.accelerator = _('<Ctrl>Q')
            toolbox.toolbar.insert(stop_button, -1)

            stop_button.show()

            self.set_toolbox(toolbox)
            toolbox.show()
        else:
            toolbox = activity.ActivityToolbox(self)
            self.set_toolbox(toolbox)
            bounce_toolbar = gtk.Toolbar()
            toolbox.add_toolbar(_('Project'), bounce_toolbar)
            toolbox.add_toolbar(_('Custom'), custom_toolbar)
            self._load_standard_buttons(bounce_toolbar)

        self._load_custom_buttons(custom_toolbar)

        # Create a canvas
        canvas = gtk.DrawingArea()
        canvas.set_size_request(gtk.gdk.screen_width(),
                                gtk.gdk.screen_height())
        self.set_canvas(canvas)
        canvas.show()
        self.show_all()

        # Read any custom fractions from the project metadata
        if 'custom' in self.metadata:
            custom = self.metadata['custom']
        else:
            custom = None

        # Initialize the canvas
        self.bounce_window = Bounce(canvas, activity.get_bundle_path(), self)

        # Restore any custom fractions
        if custom is not None:
            _logger.debug('Restoring custom data: %s', custom)
            fractions = custom.split(',')
            for f in fractions:
                self.bounce_window.add_fraction(f)

    def _load_standard_buttons(self, toolbar):
        ''' Load buttons onto whichever toolbar we are using '''
        self.fraction_button = _radio_factory('fraction', toolbar,
                                              self._fraction_cb,
                                              tooltip=_('fractions'),
                                              group=None)
        self.percent_button = _radio_factory('percent', toolbar,
                                             self._percent_cb,
                                             tooltip=_('percents'),
                                             group=self.fraction_button)

        _separator_factory(toolbar, expand=False, visible=True)

        self.challenge = _label_factory(toolbar, '')
        self.reset_label(0.5)

    def _load_custom_buttons(self, toolbar):
        ''' Entry fields and buttons for adding custom fractions '''
        self.numerator = _entry_factory('', toolbar, tooltip=_('numerator'))
        _label_factory(toolbar, '   /   ')
        self.denominator = _entry_factory('', toolbar,
                                          tooltip=_('denominator'))
        _separator_factory(toolbar, expand=False, visible=False)
        self.enter_button = _button_factory('list-add', toolbar,
                                           self._add_fraction_cb,
                                           tooltip=_('add new fraction'),
                                           accelerator='Return')

    def _fraction_cb(self, arg=None):
        ''' Set fraction mode '''
        self.bounce_window.mode = 'fractions'

    def _percent_cb(self, arg=None):
        ''' Set percent mode '''
        self.bounce_window.mode = 'percents'

    def _add_fraction_cb(self, arg=None):
        ''' Read entries and add a fraction to the list '''
        try:
            numerator = int(self.numerator.get_text().strip())
        except ValueError:
            self.numerator.set_text('NAN')
            numerator = 0
        try:
            denominator = int(self.denominator.get_text().strip())
        except ValueError:
            self.denominator.set_text('NAN')
            denominator = 1
        if denominator == 0:
            self.denominator.set_text('ZDE')
        if numerator > denominator:
            numerator = 0
        if numerator > 0 and denominator > 1:
            self.bounce_window.add_fraction('%d/%d' % (numerator, denominator))
            if 'custom' in self.metadata:  # Save to Journal
                self.metadata['custom'] = '%s,%d/%d' % (
                    self.metadata['custom'], numerator, denominator)
            else:
                self.metadata['custom'] = '%d/%d' % (numerator, denominator)

    def reset_label(self, fraction):
        ''' update the challenge label '''
        self.challenge.set_label(_('Bounce the ball to a position \
%(fraction)s of the way from the left side of the bar.') \
                                     % {'fraction': fraction})

    def __visibility_notify_cb(self, window, event):
        ''' Callback method for when the activity's visibility changes. '''
        _logger.debug('%s', str(event.state))
        return

        '''
        # Awaiting resolution of #2570
        if event.state == gtk.gdk.VISIBILITY_FULLY_OBSCURED:
            _logger.debug('pause it')
            self.bounce_window.pause()
        elif event.state in \
            [gtk.gdk.VISIBILITY_UNOBSCURED, gtk.gdk.VISIBILITY_PARTIAL]:
            if not self.bounce_window.paused:
                _logger.debug('unpause it')
                self.challenge.set_label(_('Click the ball to continue'))
        '''
