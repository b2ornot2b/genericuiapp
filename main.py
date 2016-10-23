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
from util import get_shared_file
if __name__ in ('__main__', '__android__'):
    # threading.Thread(target=ishell.listen).start()
    try: shared_formbuilder_csv = get_shared_file()
    except:
        shared_formbuilder_csv = None
        traceback.print_exc()
    print('shared_formbuilder_csv {}'.format(shared_formbuilder_csv))
    GenericUIApp(formbuilder_csv=shared_formbuilder_csv).run()
