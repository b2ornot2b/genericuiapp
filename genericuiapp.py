from __future__ import print_function

from kivy.app import App

from updater import update_from_sdcard
from genericui import GenericUI
from keyboard import Keyboard

class GenericUIApp(App):
    def build(self):
        return GenericUI(info="value")

    def on_start(self):
        win = self.root.get_root_window()
        win.set_vkeyboard_class(Keyboard)
        try:
            update_from_sdcard()
        except Exception:
            import traceback
            traceback.print_exc()

    def on_pause(self):
        print('on_pause')
        return True

    def on_resume(self):
        print('on_resume')
        return True

