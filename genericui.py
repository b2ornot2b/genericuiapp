from __future__ import print_function


from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.logger import Logger
import functools

from keyboard import Keyboard

class GenericUI(BoxLayout):
    def __init__(self, *a, **k):
        k.setdefault('cols', 2)
        super(GenericUI, self).__init__(*a, **k)
        self.bind(on_barcode_scan=self.on_barcode_scan)
        self.create_ui()

    def on_size(self, w, size):
        orientation = 'portrait' if size[0] < size[1] else 'landscape'
        Logger.info('GenericUI.on_size {} => {}'.format(orientation, size))
        Clock.schedule_once(functools.partial(Keyboard.Resize, orientation, size), 0)

    def on_barcode_scan(self, barcode, *args):
        Logger.info('GenericUI.on_barcode_scan {}'.format(barcode))

    def create_ui(self):
        self.sm = ScreenManager()
        self.sm.add_widget(self.get_home_screen())
        self.add_widget(self.sm)
        #ti = Input()
        #self.add_widget(ti)

    def get_home_screen(self):
        home = Screen(title="Home")
        btn = Button(text="OK")
        home.add_widget(btn)
        return home
