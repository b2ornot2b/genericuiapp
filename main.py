from __future__ import print_function
import kivy
kivy.require('1.0.6')
from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'dock')

import os.path
import shutil
b2kbd_json = os.path.join(kivy.kivy_data_dir, 'keyboards', 'b2kbd.json')
if not os.path.exists(b2kbd_json):
    try:
        shutil.copyfileobj(open('b2kbd.json'), open(b2kbd_json, 'w'))
        Config.set('kivy', 'keyboard_layout', 'b2kbd')
    except IOError: 
        pass


print('Keyboard layout: {}'.format(Config.get('kivy', 'keyboard_layout')))

__version__ = '0.1'

from kivy.logger import Logger
from kivy.app import App
from kivy.uix.label import Label
from kivy.properties import ObjectProperty

import threading

from kivy.logger import Logger
def _pre_logger(*a, **k): Logger.debug('{} {}'.format(a, k))
Log, Status = _pre_logger, _pre_logger

def __threaded_main(target_fn, a, k):
    import jnius
    try: target_fn(*a, **k)
    finally: jnius.detach()

def run_on_new_thread(target_fn, *a, **k):
    threading.Thread(target=__threaded_main, args=(target_fn, a, k,) ).start()

def get_sdcard_path():
    try:
        from jnius import autoclass
        Environment = autoclass('android.os.Environment')
        sdpath = Environment.get_running_app().getExternalStorageDirectory()
    except:
        sdpath = App.get_running_app().user_data_dir
    print('SDCard path {}'.format(sdpath))
    return sdpath

def android_share(to=None, subject=None, body=None, attachment=None):
    Log('to:{} subject:{} body:{}'.format(to, subject, body))
    from jnius import autoclass, cast

    PythonActivity = autoclass('org.renpy.android.PythonActivity')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    String = autoclass('java.lang.String')
    File = autoclass('java.io.File')


    intent = Intent()
    intent.setAction(Intent.ACTION_SEND)
    if to: intent.putExtra(Intent.EXTRA_EMAIL, [String(to)])
    if subject: intent.putExtra(Intent.EXTRA_SUBJECT, cast('java.lang.CharSequence', String(subject)))
    if body: intent.putExtra(Intent.EXTRA_TEXT, cast('java.lang.CharSequence', String(body)))
    if attachment:
        uri = Uri.fromFile(File(attachment))
        intent.putExtra(Intent.EXTRA_STREAM, cast('android.os.Parcelable', uri));
        intent.setType('application/octet-stream')

    currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
    currentActivity.startActivity(intent)


### START keyboard.py

import weakref
from kivy.uix.vkeyboard import VKeyboard
from kivy.properties import ListProperty
from kivy.clock import Clock
import functools

class Keyboard(VKeyboard):
    orientation = None
    __instance_ref = None
    margin_hint = ListProperty([.05, .01, .05, .01])
    def __init__(self, **kwargs):
        Keyboard.__instance_ref = weakref.ref(self)
        super(Keyboard, self).__init__(**kwargs)

        win = self.get_root_window()
        if win:
            orientation = 'portrait' if win.size[0] < win.size[1] else 'landscape'
            Clock.schedule_once(functools.partial(Keyboard.Resize, orientation, win.size), 0)

    #def refresh(self, force=False):
    #    super(Keyboard, self).refresh(force)

    @classmethod
    def Resize(cls, orientation, size, *args):
        if cls.__instance_ref:
            keyboard = cls.__instance_ref()
            if keyboard:
                keyboard.height = 500 if orientation == 'portrait' else 200
                Logger.info('Keyboard.Resize {} {} => {}x{}'.format(orientation, size, keyboard.width, keyboard.height))
                keyboard.setup_mode()
                keyboard.refresh(True)


### START genericui.py

from kivy.uix.scrollview import ScrollView
from kivy.properties import StringProperty
from kivy.lang import Builder
Builder.load_string('''
<ScrollableLabel>:
    Label:
        markup: True
        size_hint_y: None
        height: self.texture_size[1]
        text_size: self.width, None
        text: root.text
''')
class ScrollableLabel(ScrollView):
    text = StringProperty('') 

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock
import functools

import time
import itertools
class GenericUI(FloatLayout):
    def __init__(self, *a, **k):
        super(GenericUI, self).__init__(*a, **k)
        ti = TextInput()
        self.add_widget(ti)

    def on_size(self, w, size):
        orientation = 'portrait' if size[0] < size[1] else 'landscape'
        Logger.info('GenericUI.on_size {} => {}'.format(orientation, size))
        Clock.schedule_once(functools.partial(Keyboard.Resize, orientation, size), 0)


### START genericuiapp.py
class GenericUIApp(App):
    def build(self):
        return GenericUI(info="value")

    def on_start(self):
        win = self.root.get_root_window()
        win.set_vkeyboard_class(Keyboard)

    def on_pause(self):
        print('on_pause')
        return True

    def on_resume(self):
        print('on_resume')
        return True

### START main.py
if __name__ in ('__main__', '__android__'):
    GenericUIApp().run()
