from __future__ import print_function

from kivy.core.window import Window
from kivy.uix.textinput import TextInput
from kivy.properties import StringProperty
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors.focus import FocusBehavior
from kivy.uix.popup import Popup
from kivy.logger import Logger
from kivy.clock import Clock

import traceback
import weakref

class FocusButton(FocusBehavior, Button):
    pass

class XTextInput(TextInput):
    def __init__(self, *a, **k):
        self.register_event_type('on_prev')
        self.register_event_type('on_next')
        super(XTextInput, self).__init__(*a, **k)
        
    def insert_text(self, substring, from_undo=False):
        Logger.info('insert_text {} {}'.format(substring, from_undo))
        if substring == '<':
            self.dispatch('on_prev')
            return
        elif substring == '>':
            self.dispatch('on_next')
            return
        return super(XTextInput, self).insert_text(substring, from_undo=from_undo)
    def on_next(self, *a): pass
    def on_prev(self, *a): pass

class PopupTextInput(Button):
    title = StringProperty("")
    text = StringProperty("")
    def __init__(self, *a, **k):
        self.titlewidget = k.pop('titlewidget', None)
        try: self.wprevref = weakref.ref(k.pop('wprev'))
        except: self.wprevref = None
        self.wnextref = None
        super(PopupTextInput, self).__init__(*a, **k)
        try:
            title = self.titlewidget.text
        except: title = ''
        self.popup_input = XTextInput(text=self.text)
        self.popup_input.bind(on_prev=self.on_previous)
        self.popup_input.bind(on_next=self.on_next)
        self.popup_input.bind(text=self.on_edit_text)
        self.popup = Popup(title=title,
                           size_hint=(.9, None),
                           height=300,
                           content=self.popup_input)

    def set_wnext(self, wnext):
        self.wnextref = weakref.ref(wnext)

    def on_next(self, *a):
        Logger.info('on_next')
        self.popup.dismiss()
        _self = self
        while _self:
            wnext = None
            try:
                wnext = _self.wnextref()
                if wnext.disabled is True: raise Exception
                wnext.show_popup()
                _self = None
            except:
                traceback.print_exc()
                _self = wnext

    def on_previous(self, *a):
        Logger.info('on_previous')
        self.popup.dismiss()
        _self = self
        while _self:
            wprev = None
            try:
                wprev = _self.wprevref()
                if wprev.disabled is True: raise Exception
                wprev.show_popup()
                _self = None
            except:
                traceback.print_exc()
                _self = wprev

    def on_title_text(self, *a):
        Logger.info('on_title_text {}'.format(a))

    def on_press(self, *a):
        Logger.info('PopupTextInput.on_press')
        Clock.schedule_once(self.show_popup, 0)

    def show_popup(self, *a):
        self.popup.open()
        Clock.schedule_once(self.show_keyboard, 0)

    def show_keyboard(self, *a):
        keyboard = Window.request_keyboard(self._keyboard_close, self.popup_input)
        Clock.schedule_once(self.set_input_focus, 0)

    def set_input_focus(self, *a):
        self.popup_input.focus = True

    def _keyboard_close(self, *a):
        Logger.info('_keyboard_close {}'.format(a))

    def hide_popup(self, *a):
        Logger.info('hide_popup')
        try: self.popup.dismiss()
        except: traceback.print_exc()

    def on_edit_text(self, w, text, *a):
        Logger.info('on_edit_text {} {} {}'.format(w, text, a))
        self.text = text
        
    def on_tw_text(w, value):
        Logger.info('on_tw_text {} {}'.format(w, value))
        self.popup.title = value

    def on_text(self, w, value):
        Logger.info('on_text {}'.format(value))
        try: self.popup_label.text = value
        except: pass
