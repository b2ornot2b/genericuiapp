from __future__ import print_function
import kivy
kivy.require('1.0.6')
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'dock')

import os.path
import shutil
b2kbd_json = os.path.join(kivy.kivy_data_dir, 'keyboards', 'b2kbd.json')
if not os.path.exists(b2kbd_json):
    try:
        shutil.copyfileobj(open('b2kbd.json'), open(b2kbd_json, 'w'))
        Config.set('kivy', 'keyboard_layout', 'b2kbd')
    except IOError: 
        pass


print('Keyboard layout: {}'.format(Config.get('kivy', 'keyboard_layout')))

__version__ = '0.1'

from genericuiapp import GenericUIApp

if __name__ in ('__main__', '__android__'):
    GenericUIApp().run()
