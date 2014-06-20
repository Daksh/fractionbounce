# -*- coding: utf-8 -*-
#Copyright (c) 2011, Walter Bender, Paulina Clares, Chris Rowe

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU General Public License
# along with this library; if not, write to the Free Software
# Foundation, 51 Franklin Street, Suite 500 Boston, MA 02110-1335 USA

from gi.repository import Gdk

from sugar3.graphics import style

from sprites import Sprite
from svg_utils import (svg_header, svg_footer, svg_rect, svg_str_to_pixbuf,
                       svg_wedge)

from gettext import gettext as _


BAR_HEIGHT = style.GRID_CELL_SIZE


class Bar():
    ''' The Bar class is used to define the bars at the bottom of the
    screen '''

    def __init__(self, sprites, width, height, scale, size,
                 colors=['#FFFFFF', '#AAAAAA']):
        ''' Initialize the 2-segment bar, labels, and mark '''
        self.sprites = sprites
        self.colors = colors[:]
        self.bars = {}
        self.screen_width = width
        self.screen_height = height
        self.scale = scale
        self.ball_size = size

        self.make_bar(2)
        self.make_wedge_mark()

    def resize_all(self):
        self.screen_width = Gdk.Screen.width()
        self.screen_height = Gdk.Screen.height() - style.GRID_CELL_SIZE

        for bar in self.bars.keys():
            self.bars[bar].hide()
        self.mark.hide()

        for bar in self.bars.keys():
            self.make_bar(bar)
        self.make_wedge_mark()

    def make_wedge_mark(self):
        ''' Make a mark to show the fraction position on the bar. '''
        dx = self.ball_size / 2.
        n = (self.screen_width - self.ball_size) / dx
        dy = (BAR_HEIGHT * self.scale) / n
        s = 3.5
        i = int(n / 2) - 1
        mark = svg_header(self.ball_size,
                          BAR_HEIGHT * self.scale + s, 1.0)
        mark += svg_wedge(dx, BAR_HEIGHT * self.scale + s,
                          s,
                          i * 2 * dy + s, (i * 2 + 1) * dy + s,
                          '#FF0000', '#FFFFFF')
        mark += svg_wedge(dx, BAR_HEIGHT * self.scale + s,
                          dx + s,
                          (i * 2 + 1) * dy + s, (i * 2 + 2) * dy + s,
                          '#FF0000', '#FFFFFF')
        mark += svg_footer()
        self.mark = Sprite(self.sprites, 0,
                           self.screen_height,  # hide off bottom of screen
                           svg_str_to_pixbuf(mark))
        self.mark.set_layer(1)

    def make_mark(self):
        ''' Make a mark to show the fraction position on the bar. '''
        mark = svg_header(self.ball_size / 2.,
                          BAR_HEIGHT * self.scale + 4, 1.0) + \
               svg_rect(self.ball_size / 2.,
                        BAR_HEIGHT * self.scale + 4, 0, 0, 0, 0,
                        '#FF0000', '#FF0000') + \
               svg_rect(1, BAR_HEIGHT * self.scale + 4, 0, 0,
                        self.ball_size / 4., 0, '#000000', '#000000') + \
               svg_footer()
        self.mark = Sprite(self.sprites, 0,
                           self.screen_height,  # hide off bottom of screen
                           svg_str_to_pixbuf(mark))
        self.mark.set_layer(1)

    def mark_width(self):
        return self.mark.rect[2]

    def bar_x(self):
        return self.bars[2].get_xy()[0]

    def bar_y(self):
        if self.bars[2].get_xy()[1] < 0:
            return self.bars[2].get_xy()[1] + 3000
        else:
            return self.bars[2].get_xy()[1]

    def width(self):
        return self.bars[2].rect[2]

    def height(self):
        return self.bars[2].rect[3]

    def show_bar(self, n):
        if n in self.bars:
            self.bars[n].move([self.bar_x(), self.bar_y()])

    def bump_bars(self, direction='up'):
        ''' when the toolbars expand and contract, we need to move the bar '''
        if direction == 'up':
            dy = -style.GRID_CELL_SIZE
        else:
            dy = style.GRID_CELL_SIZE
        for bar in self.bars:
            self.bars[bar].move_relative([0, dy])
        self.mark.move_relative([0, dy])

    def hide_bars(self):
        ''' Hide all of the bars '''
        for bar in self.bars:
            if self.bars[bar].get_xy()[1] > 0:
                self.bars[bar].move_relative([0, -3000])

    def get_bar(self, nsegments):
        ''' Return a bar with n segments '''
        if nsegments not in self.bars:
            self.make_bar(nsegments)
        return self.bars[nsegments]

    def make_bar(self, nsegments):
        return self.make_wedge_bar(nsegments)

    def make_rect_bar(self, nsegments):
        ''' Create a bar with n segments '''
        svg = svg_header(self.screen_width - self.ball_size,
                         BAR_HEIGHT * self.scale, 1.0)
        dx = (self.screen_width - self.ball_size) / float(nsegments)
        for i in range(int(nsegments) / 2):
            svg += svg_rect(dx, BAR_HEIGHT * self.scale, 0, 0,
                            i * 2 * dx, 0, self.colors[0], self.colors[0])
            svg += svg_rect(dx, BAR_HEIGHT * self.scale, 0, 0,
                            (i * 2 + 1) * dx, 0, self.colors[1], self.colors[1])
        if int(nsegments) % 2 == 1:  # odd
            svg += svg_rect(dx, BAR_HEIGHT * self.scale, 0, 0,
                            (i * 2 + 2) * dx, 0, self.colors[0], self.colors[0])
        svg += svg_footer()

        self.bars[nsegments] = Sprite(self.sprites, 0, 0,
                                      svg_str_to_pixbuf(svg))
        self.bars[nsegments].move(
            (int(self.ball_size / 2), self.screen_height - \
                 int((self.ball_size + self.height()) / 2)))

    def make_wedge_bar(self, nsegments):
        ''' Create a wedged-shaped bar with n segments '''
        s = 3.5  # add provision for stroke width
        svg = svg_header(self.screen_width - self.ball_size,
                         BAR_HEIGHT * self.scale + s, 1.0)
        dx = (self.screen_width - self.ball_size) / float(nsegments)
        dy = (BAR_HEIGHT * self.scale) / float(nsegments)
        for i in range(int(nsegments) / 2):
            svg += svg_wedge(dx, BAR_HEIGHT * self.scale + s,
                             i * 2 * dx + s,
                             i * 2 * dy + s, (i * 2 + 1) * dy + s,
                             '#000000', '#FFFFFF')
            svg += svg_wedge(dx, BAR_HEIGHT * self.scale + s,
                             (i * 2 + 1) * dx + s,
                             (i * 2 + 1) * dy + s, (i * 2 + 2) * dy + s,
                             '#000000', '#FFFFFF')
        if int(nsegments) % 2 == 1:  # odd
            svg += svg_wedge(dx, BAR_HEIGHT * self.scale + s,
                             (i * 2 + 2) * dx + s,
                             (i * 2 + 2) * dy + s, BAR_HEIGHT * self.scale + s,
                             '#000000', '#FFFFFF')
        svg += svg_footer()

        self.bars[nsegments] = Sprite(self.sprites, 0, 0,
                                      svg_str_to_pixbuf(svg))
        self.bars[nsegments].set_layer(2)
        self.bars[nsegments].set_label_attributes(18, horiz_align="left", i=0)
        self.bars[nsegments].set_label_attributes(18, horiz_align="right", i=1)
        self.bars[nsegments].set_label_color('black', i=0)
        self.bars[nsegments].set_label_color('white', i=1)
        self.bars[nsegments].set_label(' 0', i=0)
        self.bars[nsegments].set_label('1 ', i=1)
        self.bars[nsegments].move(
            (int(self.ball_size / 2),
             self.screen_height - BAR_HEIGHT * self.scale))
                 # int((self.ball_size + self.height()) / 2)))
