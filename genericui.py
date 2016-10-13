from __future__ import print_function

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.logger import Logger
import functools

from keyboard import Keyboard

class GenericUI(FloatLayout):
    def __init__(self, *a, **k):
        super(GenericUI, self).__init__(*a, **k)
        ti = TextInput()
        self.add_widget(ti)

    def on_size(self, w, size):
        orientation = 'portrait' if size[0] < size[1] else 'landscape'
        Logger.info('GenericUI.on_size {} => {}'.format(orientation, size))
        Clock.schedule_once(functools.partial(Keyboard.Resize, orientation, size), 0)

