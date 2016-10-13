from __future__ import print_function

__version__ = '0.1'

import kivy
kivy.require('1.0.6')

from keyboard import keyboard_init
if __name__ in ('__main__', '__android__'):
    keyboard_init()

from genericuiapp import GenericUIApp
if __name__ in ('__main__', '__android__'):
    GenericUIApp().run()
