# -*- coding: utf-8 -*-
#Copyright (c) 2011, Walter Bender, Paulina Clares, Chris Rowe
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

EASY = [('1/2', 0.5, 12), ('1/3', 1 / 3., 12), ('3/4', 0.75, 12),
        ('1/4', 0.25, 12), ('2/3', 2 / 3., 12), ('1/6', 1 / 6., 12),
        ('5/6', 5 / 6., 12)]
MEDIUM = [('2/8', 0.25, 12), ('2/4', 0.5, 12),  ('3/6', 0.5, 12),
          ('6/12', 0.5, 12), ('4/6', 2 / 3., 12), ('2/6', 1 / 3., 12),
          ('5/12', 5 / 12., 12), ('3/12', 0.25, 12), ('7/12', 7 / 12., 12),
          ('8/12', 2 / 3., 12), ('4/8', 0.5, 12), ('6/12', 0.5, 12),
          ('9/12', 0.75, 12), ('2/12', 1 / 6., 12), ('4/12', 1 / 3., 12),
          ('10/12', 5 / 6., 12), ('11/12', 11 / 12., 12)]
HARD = [('2/5', 0.4, 10), ('4/5', 0.8, 10), ('3/5', 0.6, 10),
        ('1/10', 0.1, 10), ('1/5', 0.2, 10), ('5/10', 0.5, 10),
        ('3/10', 0.3, 10), ('7/10', 0.7, 10), ('8/10', 0.8, 10),
        ('2/7', 2 / 7., 14), ('4/7', 4 / 7., 14), ('3/7', 3 / 7., 14),
        ('1/14', 1 / 14., 14), ('1/7', 1 / 7., 14), ('5/14', 5 / 14., 14),
        ('3/14', 3 / 14., 14), ('7/14', 0.5, 14), ('8/14', 4 / 7., 14),
        ('1/8', 0.125, 12), ('3/8', 0.375, 12), ('5/8', 0.625, 12)]
EXPERT = 100  # after many correct answers, don't segment the bar
BAR_HEIGHT = 20
STEPS = 100.  # number of time steps per bounce rise and fall
STEP_PAUSE = 50  # milliseconds between steps
BOUNCE_PAUSE = 3000  # milliseconds between bounces
ANIMATION = {10: (0, 1), 15: (1, 2), 20: (2, 1), 25: (1, 2), 30: (2, 1),
             35: (1, 2), 40: (2, 3), 45: (3, 4), 50: (4, 3), 55: (3, 4),
             60: (4, 3), 65: (3, 4), 70: (4, 5), 75: (5, 6), 80: (6, 5),
             85: (5, 6), 90: (6, 7)}
ACCELEROMETER_DEVICE = '/sys/devices/platform/lis3lv02d/position'
CRASH = 'crash.ogg'
LAUGH = 'laugh.ogg'
BUBBLES = 'bubbles.ogg'

import gtk
from random import uniform
import os
import gobject

from play_audio import play_audio_from_file

from gettext import gettext as _

import logging
_logger = logging.getLogger('fractionbounce-activity')

try:
    from sugar.graphics import style
    GRID_CELL_SIZE = style.GRID_CELL_SIZE
except ImportError:
    GRID_CELL_SIZE = 0

from sprites import Sprites, Sprite


def _svg_str_to_pixbuf(svg_string):
    ''' Load pixbuf from SVG string '''
    pl = gtk.gdk.PixbufLoader('svg')
    pl.write(svg_string)
    pl.close()
    pixbuf = pl.get_pixbuf()
    return pixbuf


def _svg_rect(w, h, rx, ry, x, y, fill, stroke):
    ''' Returns an SVG rectangle '''
    svg_string = '       <rect\n'
    svg_string += '          width="%f"\n' % (w)
    svg_string += '          height="%f"\n' % (h)
    svg_string += '          rx="%f"\n' % (rx)
    svg_string += '          ry="%f"\n' % (ry)
    svg_string += '          x="%f"\n' % (x)
    svg_string += '          y="%f"\n' % (y)
    svg_string += _svg_style('fill:%s;stroke:%s;' % (fill, stroke))
    return svg_string


def _svg_header(w, h, scale, hscale=1.0):
    ''' Returns SVG header; some beads are elongated (hscale) '''
    svg_string = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg_string += '<!-- Created with Python -->\n'
    svg_string += '<svg\n'
    svg_string += '   xmlns:svg="http://www.w3.org/2000/svg"\n'
    svg_string += '   xmlns="http://www.w3.org/2000/svg"\n'
    svg_string += '   version="1.0"\n'
    svg_string += '   width="%f"\n' % (w * scale)
    svg_string += '   height="%f">\n' % (h * scale * hscale)
    svg_string += '<g\n       transform="matrix(%f,0,0,%f,0,0)">\n' % (
                                  scale, scale)
    return svg_string


def _svg_footer():
    ''' Returns SVG footer '''
    svg_string = '</g>\n'
    svg_string += '</svg>\n'
    return svg_string


def _svg_style(extras=''):
    ''' Returns SVG style for shape rendering '''
    return 'style="%s"/>\n' % (extras)


class Bounce():
    ''' The Bounce class is used to define the ball and the user
    interaction. '''

    def __init__(self, canvas, path, parent=None):
        ''' Initialize the canvas and set up the callbacks. '''
        self.activity = parent

        if parent is None:        # Starting from command line
            self.sugar = False
            self.canvas = canvas
        else:                     # Starting from Sugar
            self.sugar = True
            self.canvas = canvas
            parent.show_all()

        self.canvas.grab_focus()

        if os.path.exists(ACCELEROMETER_DEVICE):
            self.accelerometer = True
        else:
            self.accelerometer = False

        self.canvas.set_flags(gtk.CAN_FOCUS)
        self.canvas.add_events(gtk.gdk.BUTTON_PRESS_MASK)
        self.canvas.add_events(gtk.gdk.BUTTON_RELEASE_MASK)
        self.canvas.add_events(gtk.gdk.POINTER_MOTION_MASK)
        self.canvas.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.canvas.add_events(gtk.gdk.KEY_RELEASE_MASK)
        self.canvas.connect('expose-event', self._expose_cb)
        self.canvas.connect('button-press-event', self._button_press_cb)
        self.canvas.connect('button-release-event', self._button_release_cb)
        self.canvas.connect('key_press_event', self._keypress_cb)
        self.canvas.connect('key_release_event', self._keyrelease_cb)
        self.width = gtk.gdk.screen_width()
        self.height = gtk.gdk.screen_height() - GRID_CELL_SIZE
        self.sprites = Sprites(self.canvas)
        self.scale = gtk.gdk.screen_height() / 900.0

        self.easter_egg = int(uniform(1, 100))
        _logger.debug('%d', self.easter_egg)

        # Find paths to sound files
        self.path_to_success = os.path.join(path, LAUGH)
        self.path_to_failure = os.path.join(path, CRASH)
        self.path_to_bubbles = os.path.join(path, BUBBLES)

        # Create the sprites we'll need
        self.smiley_graphic = _svg_str_to_pixbuf(svg_from_file(
                os.path.join(path, 'smiley.svg')))

        self.ball = Sprite(self.sprites, 0, 0,
                           _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball.svg'))))
        self.ball.set_layer(1)
        self.ball.set_label_attributes(24)

        self.cells = []  # Easter Egg animation
        self.cells.append(Sprite(self.sprites, 0, 0,
                                   _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball1.svg')))))
        self.cells.append(Sprite(self.sprites, 0, 0,
                                   _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball2.svg')))))
        self.cells.append(Sprite(self.sprites, 0, 0,
                                   _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball2a.svg')))))
        self.cells.append(Sprite(self.sprites, 0, 0,
                                   _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball3.svg')))))
        self.cells.append(Sprite(self.sprites, 0, 0,
                                   _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball3a.svg')))))
        self.cells.append(Sprite(self.sprites, 0, 0,
                                   _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball4.svg')))))
        self.cells.append(Sprite(self.sprites, 0, 0,
                                   _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball4a.svg')))))
        self.cells.append(Sprite(self.sprites, 0, 0,
                                   _svg_str_to_pixbuf(svg_from_file(
                    os.path.join(path, 'basketball5.svg')))))
        for spr in self.cells:
            spr.set_layer(1)
            spr.move((0, self.height))  # move animation cells off screen
        self.frame = 0

        mark = _svg_header(self.ball.rect[2] / 2, BAR_HEIGHT * self.scale + 4,
                           1.0) + \
               _svg_rect(self.ball.rect[2] / 2,
                         BAR_HEIGHT * self.scale + 4, 0, 0, 0, 0,
                         '#FF0000', '#FF0000') + \
               _svg_footer()
        self.mark = Sprite(self.sprites, 0,
                           self.height,  # hide off bottom of screen
                           _svg_str_to_pixbuf(mark))
        self.mark.set_layer(2)

        # divide into two segments
        self.bar = Sprite(self.sprites, 0, 0,
                          _svg_str_to_pixbuf(self._gen_bar(2)))
        # divide into twelve segments
        self.bar12 = Sprite(self.sprites, 0, 0,
                            _svg_str_to_pixbuf(self._gen_bar(12)))
        # divide into ten segments
        self.bar10 = Sprite(self.sprites, 0, 0,
                            _svg_str_to_pixbuf(self._gen_bar(10)))
        # divide into fourteen segments
        self.bar14 = Sprite(self.sprites, 0, 0,
                            _svg_str_to_pixbuf(self._gen_bar(14)))

        hoffset = int((self.ball.rect[3] + self.bar.rect[3]) / 2)
        self.bar.move((int(self.ball.rect[2] / 2), self.height - hoffset))
        self.bar12.move((int(self.ball.rect[2] / 2), self.height - hoffset))
        self.bar10.move((int(self.ball.rect[2] / 2), self.height - hoffset))
        self.bar14.move((int(self.ball.rect[2] / 2), self.height - hoffset))
        num = _svg_header(BAR_HEIGHT * self.scale, BAR_HEIGHT * self.scale,
                           1.0) + \
              _svg_rect(BAR_HEIGHT * self.scale,
                        BAR_HEIGHT * self.scale, 0, 0, 0, 0,
                        'none', 'none') + \
              _svg_footer()
        self.left = Sprite(self.sprites, int(self.ball.rect[2] / 4),
                           self.height - hoffset, _svg_str_to_pixbuf(num))
        self.left.set_label('0')
        self.right = Sprite(self.sprites,
                            self.width - int(self.ball.rect[2] / 2),
                            self.height - hoffset, _svg_str_to_pixbuf(num))
        self.right.set_label('1')

        self.ball_y_max = self.bar.rect[1] - self.ball.rect[3]
        self.ball.move((int((self.width - self.ball.rect[2]) / 2),
                        self.ball_y_max))

        self.challenges = []
        for challenge in EASY:
            self.challenges.append(challenge)
        self.dx = 0  # ball horizontal trajectory
        self.fraction = 0.5  # the target of the current challenge
        self.count = 0  # number of bounces played
        self.correct = 0  # number of correct answers
        self.press = None  # sprite under mouse click
        self.new_bounce = False

        delta = self.height / STEPS
        self.ddy = 6.67 * delta / STEPS  # acceleration (with dampening)
        self.dy = self.ddy * (1 - STEPS) / 2  # initial step size
        _logger.debug('delta: %f, ddy: %f, dy: %f', delta, self.ddy, self.dy)

        self.activity.challenge.set_label(_("Click the ball to start"))

    def _gen_bar(self, nsegments):
        ''' Return a bar with n segments '''
        svg = _svg_header(self.width - self.ball.rect[2], BAR_HEIGHT, 1.0)
        dx = (self.width - self.ball.rect[2]) / nsegments
        for i in range(nsegments / 2):
            svg += _svg_rect(dx, BAR_HEIGHT * self.scale, 0, 0,
                             i * 2 * dx, 0, '#FFFFFF', '#FFFFFF')
            svg += _svg_rect(dx, BAR_HEIGHT * self.scale, 0, 0,
                             (i * 2 + 1) * dx, 0, '#AAAAAA', '#AAAAAA')
        svg += _svg_footer()
        return svg

    def _button_press_cb(self, win, event):
        ''' Callback to handle the button presses '''
        win.grab_focus()
        x, y = map(int, event.get_coords())
        self.press = self.sprites.find_sprite((x, y))
        return True

    def _button_release_cb(self, win, event):
        ''' Callback to handle the button releases '''
        win.grab_focus()
        x, y = map(int, event.get_coords())
        if self.press is not None:
            if self.count == 0 and self.press == self.ball:
                self._choose_a_fraction()
                self._move_ball()
        return True

    def _move_ball(self):
        ''' Move the ball and test boundary conditions '''
        if self.new_bounce:
            self.mark.move((0, self.height))  # hide the mark
            self._choose_a_fraction()
            self.new_bounce = False
            self.dy = self.ddy * (1 - STEPS) / 2  # initial step size

        if self.accelerometer:
            fh = open(ACCELEROMETER_DEVICE)
            string = fh.read()
            xyz = string[1:-2].split(',')
            self.dx = int(float(xyz[0]) / 18.)
            fh.close()

        if self.ball.get_xy()[0] + self.dx > 0 and \
           self.ball.get_xy()[0] + self.dx < self.width - self.ball.rect[2]:
            self.ball.move_relative((self.dx, self.dy))
        else:
            self.ball.move_relative((0, self.dy))

        self.dy += self.ddy

        if self.ball.get_xy()[1] >= self.ball_y_max:
            # hit the bottom
            self.ball.move((self.ball.get_xy()[0], self.ball_y_max))
            self._test()
            self.new_bounce = True

            if self._easter_egg_test():
                self._animate()
            else:
                gobject.timeout_add(  # wait less and less as game goes on
                    max(STEP_PAUSE, BOUNCE_PAUSE - self.count * STEP_PAUSE),
                    self._move_ball)
        else:
            gobject.timeout_add(STEP_PAUSE, self._move_ball)

    def _animate(self):
        ''' A little Easter Egg just for fun. '''
        if self.new_bounce:
            self.dy = self.ddy * (1 - STEPS) / 2  # initial step size
            self.new_bounce = False
            self.frame = 0
            self.frame_counter = 0
            self.cells[self.frame].move(self.ball.get_xy())
            self.ball.move((self.ball.get_xy()[0], self.height))
            play_audio_from_file(self, self.path_to_bubbles)

        if self.accelerometer:
            fh = open(ACCELEROMETER_DEVICE)
            string = fh.read()
            xyz = string[1:-2].split(',')
            self.dx = int(float(xyz[0]) / 18.)
            fh.close()
        else:
            self.dx = int(uniform(-5, 5))
        self.cells[self.frame].move_relative((self.dx, self.dy))
        self.dy += self.ddy

        self.frame_counter += 1
        if self.frame_counter in ANIMATION:
            self._switch_cells(ANIMATION[self.frame_counter])

        if self.cells[self.frame].get_xy()[1] >= self.ball_y_max:
            # hit the bottom
            self.ball.move((self.ball.get_xy()[0], self.ball_y_max))
            for spr in self.cells:
                spr.move((0, self.height))  # hide the animation frames
            _logger.debug('%d', self.frame_counter)
            self._test()
            self.new_bounce = True
            gobject.timeout_add(BOUNCE_PAUSE, self._move_ball)
        else:
            gobject.timeout_add(STEP_PAUSE, self._animate)

    def _switch_cells(self, cells):
        ''' Switch between cells in the animation '''
        self.cells[cells[1]].move(self.cells[cells[0]].get_xy())
        self.cells[cells[0]].move((0, self.height))
        self.frame = cells[1]

    def _choose_a_fraction(self):
        ''' Select a new fraction challenge from the table '''
        n = int(uniform(0, len(self.challenges)))
        self.activity.reset_label(self.challenges[n][0])
        self.ball.set_label(self.challenges[n][0])
        self.fraction = self.challenges[n][1]

        if self.correct > EXPERT:  # show two-segment bar
            self.bar.set_layer(0)
            self.bar10.set_layer(-1)
            self.bar12.set_layer(-1)
            self.bar14.set_layer(-1)
        elif self.challenges[n][2] == 12:  # show twelve-segment bar
            self.bar.set_layer(-1)
            self.bar10.set_layer(-1)
            self.bar12.set_layer(0)
            self.bar14.set_layer(-1)
        elif self.challenges[n][2] == 10:  # show ten-segment bar
            self.bar.set_layer(-1)
            self.bar10.set_layer(0)
            self.bar12.set_layer(-1)
            self.bar14.set_layer(-1)
        else:  # show fourteen-segment bar
            self.bar.set_layer(-1)
            self.bar10.set_layer(-1)
            self.bar12.set_layer(-1)
            self.bar14.set_layer(0)

    def _easter_egg_test(self):
        ''' Test to see if we show the Easter Egg '''
        delta = self.ball.rect[2] / 8
        x = self.ball.get_xy()[0] + self.ball.rect[2] / 2
        f = self.bar.rect[2] * self.easter_egg / 100.
        if x > f - delta and x < f + delta:
            return True
        else:
            return False

    def _test(self):
        ''' Test to see if we estimated correctly '''
        delta = self.ball.rect[2] / 4
        x = self.ball.get_xy()[0] + self.ball.rect[2] / 2
        f = self.ball.rect[2] / 2 + int(self.fraction * self.bar.rect[2])
        self.mark.move((int(f - self.mark.rect[2] / 2), self.bar.rect[1] - 2))
        if x > f - delta and x < f + delta:
            smiley = Sprite(self.sprites, 0, 0, self.smiley_graphic)
            x = int(self.count * 25 % self.width)
            y = int(self.count / int(self.width / 25)) * 25
            smiley.move((x, y))
            smiley.set_layer(-1)
            self.correct += 1
            gobject.idle_add(play_audio_from_file, self, self.path_to_success)
        else:
            gobject.idle_add(play_audio_from_file, self, self.path_to_failure)


        # after enough correct answers, up the difficulty
        if self.correct == len(EASY) * 2:
            for challenge in MEDIUM:
                self.challenges.append(challenge)
            _logger.debug('%s', self.challenges)
        elif self.correct == len(EASY) * 4:
            for challenge in HARD:
                self.challenges.append(challenge)
            _logger.debug('%s', self.challenges)

        self.count += 1
        self.dx = 0  # stop horizontal movement between bounces

    def _keypress_cb(self, area, event):
        ''' Keypress: moving the slides with the arrow keys '''
        k = gtk.gdk.keyval_name(event.keyval)
        if k in ['h', 'Left', 'KP_Left']:
            self.dx = -5
        elif k in ['l', 'Right', 'KP_Right']:
            self.dx = 5
        elif k in ['KP_Page_Up', 'Return']:
            self._choose_a_fraction()
            self._move_ball()
        else:
            self.dx = 0
        return True

    def _keyrelease_cb(self, area, event):
        ''' Keyrelease: stop horizontal movement '''
        self.dx = 0
        return True

    def _expose_cb(self, win, event):
        ''' Callback to handle window expose events '''
        self.sprites.redraw_sprites(event.area)
        return True

    def _destroy_cb(self, win, event):
        ''' Callback to handle quit '''
        gtk.main_quit()


def svg_from_file(pathname):
    ''' Read SVG string from a file '''
    f = file(pathname, 'r')
    svg = f.read()
    f.close()
    return(svg)
