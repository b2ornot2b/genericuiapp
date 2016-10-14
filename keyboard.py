from __future__ import print_function

import kivy
import os.path
import shutil

def keyboard_init():
    print('keyboard_init')
    from kivy.config import Config
    Config.set('kivy', 'keyboard_mode', 'dock')

    kbd = 'b2simplekbd'
    kbd_json = '{}.json'.format(kbd)
    b2kbd_json = os.path.join(kivy.kivy_data_dir, 'keyboards', kbd_json)
    if not os.path.exists(b2kbd_json):
        try:
            shutil.copyfileobj(open(kbd_json), open(b2kbd_json, 'w'))
            Config.set('kivy', 'keyboard_layout', kbd)
        except IOError: 
            pass
    print('Keyboard layout: {}'.format(Config.get('kivy', 'keyboard_layout')))
    #from kivy.core.window import Window
    #try: print('softinput_mode {}'.format(Window.softinput_mode))
    #except: pass
    #Window.softinput_mode = 'below_target'


from kivy.uix.vkeyboard import VKeyboard
from kivy.properties import ListProperty
from kivy.clock import Clock
from kivy.logger import Logger

import weakref
import functools

class Keyboard(VKeyboard):
    orientation = None
    __instance_ref = None
    margin_hint = ListProperty([.05, .01, .05, .01])
    def __init__(self, **kwargs):
        Keyboard.__instance_ref = weakref.ref(self)
        super(Keyboard, self).__init__(**kwargs)
        Clock.schedule_once(self.__check_orientation, 0)

    def __check_orientation(self, *args):
        win = self.get_root_window()
        if win:
            orientation = 'portrait' if win.size[0] < win.size[1] else 'landscape'
            Clock.schedule_once(functools.partial(Keyboard.Resize, orientation, win.size), 0)

    @classmethod
    def Resize(cls, orientation, size, *args):
        if cls.__instance_ref:
            keyboard = cls.__instance_ref()
            if keyboard:
                keyboard.height = 500 if orientation == 'portrait' else 200
                Logger.info('Keyboard.Resize {} {} => {}x{}'.format(orientation, size, keyboard.width, keyboard.height))
                keyboard.setup_mode()
                keyboard.refresh(True)
