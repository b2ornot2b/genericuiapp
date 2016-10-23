from __future__ import print_function

from kivy.app import App
from kivy.core.window import Window
# Window.softinput_mode = 'below_target'
from kivy.clock import Clock
from kivy.logger import Logger
#import kivy.modules.webdebugger
#from kivy.modules.webdebugger import start as webdebugger_start
#from kivy.modules._webdebugger import FlaskThread as WebDebuggerFlaskThread, app as WebDebuggerApp
#def FlaskThreadRun(self, *a, **k):
#    Clock.schedule_interval(self.dump_metrics, .1)
#    WebDebuggerApp.run(host="0.0.0.0", debug=True, use_debugger=True, use_reloader=False)
#WebDebuggerFlaskThread.run = FlaskThreadRun

from updater import update
from genericui import GenericUI
from keyboard import Keyboard
from util import run_on_new_thread

import functools

class GenericUIApp(App):
    def __init__(self, *a, **k):
        self.formbuilder_csv = k.pop('formbuilder_csv', None)
        print('GenericUIApp formbuilder_csv={}'.format(type(self.formbuilder_csv)))
        super(GenericUIApp, self).__init__(*a, **k)
    def build(self):
        # webdebugger_start(None, self)
        self.__base_widget = GenericUI(info="value", formbuilder_csv=self.formbuilder_csv)
        return self.__base_widget

    def on_start(self):
        run_on_new_thread(update)
        win = self.root.get_root_window()
        win.set_vkeyboard_class(Keyboard)
        win.softinput_mode = 'pan'
        win.bind(on_key_down=self.on_key_down)
        self.__complete_key_input_event = None
        self.__key_input = ''


    def on_pause(self):
        Logger.info('on_pause')
        return True

    def on_resume(self):
        Logger.info('on_resume')
        return True

    def on_key_down(self, win, key, scancode=None, codepoint=None, modifier=None, *args):
        # print('on_key_down {} {} {} {} {} {}'.format(win, key,scancode,codepoint,modifier,args))
        if key == 27:
            print('BACK')
            return self.__base_widget.on_back()
        try:
            self.__key_input += codepoint # chr(key)
        except:
            return False
        if self.__complete_key_input_event:
            self.__complete_key_input_event.cancel()
        self.__complete_key_input_event = Clock.schedule_once(self.__complete_key_input, .2)
        return False

    def __complete_key_input(self, *args):
        self.on_barcode_scan(self.__key_input)
        self.__key_input = ''

    def on_barcode_scan(self, barcode):
        Logger.info('on_barcode_scan {}'.format(barcode))
        if len(barcode):
            Clock.schedule_once(functools.partial(self.__base_widget.on_barcode_scan, barcode), -1)
        #win = self.root.get_root_window()
        #self.__base_widget.dispatch('on_barcode_scan', barcode)
