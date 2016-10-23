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
import traceback
from genericuiapp import GenericUIApp
from util import get_android_shared_file
if __name__ in ('__main__', '__android__'):
    # threading.Thread(target=ishell.listen).start()
    try:
        shared_formbuilder_csv = get_android_shared_file()
        if shared_formbuilder_csv:
            print('shared_formbuilder_csv {}'.format(len(shared_formbuilder_csv)))
    except:
        shared_formbuilder_csv = None
        traceback.print_exc()
    GenericUIApp(formbuilder_csv=shared_formbuilder_csv).run()
