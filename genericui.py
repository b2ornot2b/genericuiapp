from __future__ import print_function


from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.logger import Logger
import functools
from kivy.modules.webdebugger import start as webdebugger_start

from keyboard import Keyboard
from kivytoast import toast

class GenericUI(ScreenManager):
    def __init__(self, *a, **k):
        super(GenericUI, self).__init__(*a, **k)
        self.bind(on_barcode_scan=self.on_barcode_scan)
        self.create_ui()

    def on_size(self, w, size):
        orientation = 'portrait' if size[0] < size[1] else 'landscape'
        Logger.info('GenericUI.on_size {} => {}'.format(orientation, size))
        Clock.schedule_once(functools.partial(Keyboard.Resize, orientation, size), 0)

    def on_barcode_scan(self, barcode, *args):
        Logger.info('GenericUI.on_barcode_scan {}'.format(barcode))
        if len(barcode):
            toast("Scanned {}".format(barcode))

    def create_ui(self):
        #self.sm = ScreenManager()
        self.add_widget(self.get_home_screen())
        #self.add_widget(self.sm)
        #ti = Input()
        #self.add_widget(ti)

    def get_home_screen(self):
        home = Screen(title="Home")
        sv = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        bl = BoxLayout(orientation="vertical", size_hint_y=None)
        btn = Button(text="OK", size_hint=(1, None), on_press=functools.partial(self.button_pressed, bl))
        bl.add_widget(btn)
        sv.add_widget(bl)
        home.add_widget(sv)
        return home

    def button_pressed(self, home, *args):
        Logger.info('button_pressed {} {}'.format(home, args))
        btn = Button(text="OK", size_hint=(1, None), on_press=self.button_pressed)
        home.add_widget(btn)

        ti = TextInput(size_hint=(1, None))
        home.add_widget(ti)


        return False

