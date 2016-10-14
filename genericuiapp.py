from __future__ import print_function

from kivy.app import App
from kivy.clock import Clock
from kivy.logger import Logger

from updater import update
from genericui import GenericUI
from keyboard import Keyboard

class GenericUIApp(App):
    def build(self):
        return GenericUI(info="value")

    def on_start(self):
        win = self.root.get_root_window()
        win.set_vkeyboard_class(Keyboard)
        self.__complete_key_input_event = None
        self.__key_input = ''
        win.bind(on_key_down=self.on_key_down)
        try:
            update()
        except Exception:
            import traceback
            traceback.print_exc()

    def on_pause(self):
        Logger.info('on_pause')
        return True

    def on_resume(self):
        Logger.info('on_resume')
        return True

    def on_key_down(self, win, key, scancode=None, codepoint=None, modifier=None, *args):
        try:
            self.__key_input += codepoint # chr(key)
        except:
            return True
        if self.__complete_key_input_event:
            self.__complete_key_input_event.cancel()
        self.__complete_key_input_event = Clock.schedule_once(self.__complete_key_input, .2)
        return True

    def __complete_key_input(self, *args):
        self.on_barcode_scan(self.__key_input)
        self.__key_input = ''

    def on_barcode_scan(self, barcode):
        Logger.info('on_barcode_scan {}'.format(barcode))
