from __future__ import print_function

__version__ = '0.1'

if __name__ in ('__main__', '__android__'):
    from kivy.config import Config
    Config.set('kivy', 'keyboard_mode', 'dock')

import kivy
kivy.require('1.9.1')

from keyboard import keyboard_init
if __name__ in ('__main__', '__android__'):
    keyboard_init()

import threading
import ishell
from genericuiapp import GenericUIApp
if __name__ in ('__main__', '__android__'):
    # threading.Thread(target=ishell.listen).start()
    GenericUIApp().run()
