from __future__ import print_function

import kivy
import os.path
import shutil
from ConfigParser import SafeConfigParser as ConfigParser

def get_keyboard_config():
    config = ConfigParser()
    config.read('app.ini')
    try: kbsetting = config.get('app', 'keyboard')
    except: kbsetting = 'dock'
    return kbsetting

def set_keyboard_config(kbsetting):
    config = ConfigParser()
    config.read('app.ini')
    try: config.add_section('app')
    except: pass
    config.set('app', 'keyboard', kbsetting)
    config.write(open('app.ini', 'w'))
    from kivy.config import Config
    Config.set('kivy', 'keyboard_mode', kbsetting)


def keyboard_init():
    mode = get_keyboard_config()
    from kivy.config import Config
    Config.set('kivy', 'keyboard_mode', mode)

    kbd = 'b2simplekbd'
    kbd_json = '{}.json'.format(kbd)
    b2kbd_json = os.path.join(kivy.kivy_data_dir, 'keyboards', kbd_json)
    print('keyboard_init {}'.format(b2kbd_json))
    if True: # not os.path.exists(b2kbd_json):
        try:
            shutil.copyfileobj(open(kbd_json), open(b2kbd_json, 'w'))
        except IOError: 
            pass
    Config.set('kivy', 'keyboard_layout', kbd)
    print('Keyboard layout: {}'.format(Config.get('kivy', 'keyboard_layout')))
    #from kivy.core.window import Window
    #try: print('softinput_mode {}'.format(Window.softinput_mode))
    #except: pass
    #Window.softinput_mode = 'below_target'


from kivy.uix.vkeyboard import VKeyboard
from kivy.uix.bubble import Bubble
from kivy.properties import ListProperty, NumericProperty, StringProperty
from kivy.clock import Clock
from kivy.logger import Logger

from kivy.uix.label import Label
from kivy.uix.bubble import Bubble
from kivy.graphics import Color, BorderImage, Canvas
from kivy.resources import resource_find
from kivy.core.image import Image

import weakref
import functools

class Keyboard(VKeyboard):
    orientation = None
    __instance_ref = None
    margin_hint = ListProperty([.05, .01, .01, .01])
    key_margin = ListProperty([0,0,0,0])
    font_size = NumericProperty('40dp')
    key_background_normal = StringProperty('atlas://data/images/defaulttheme/player-background')
    key_background_down = StringProperty('atlas://data/images/defaulttheme/progressbar')
    key_disabled_background_normal = StringProperty('atlas://data/images/defaulttheme/player-background')
    background = StringProperty('atlas://data/images/defaulttheme/modalview-background')
    def __init__(self, **kwargs):
        Keyboard.__instance_ref = weakref.ref(self)
        super(Keyboard, self).__init__(**kwargs)
        Clock.schedule_once(self.__check_orientation, 0)

    def draw_keys(self):
        layout = self.available_layouts[self.layout]
        layout_rows = layout['rows']
        layout_geometry = self.layout_geometry
        layout_mode = self.layout_mode

        # draw background
        w, h = self.size

        background = resource_find(self.background_disabled
                                   if self.disabled else
                                   self.background)
        texture = Image(background, mipmap=True).texture
        self.background_key_layer.clear()
        with self.background_key_layer:
            Color(*self.background_color)
            BorderImage(texture=texture, size=self.size,
                        border=self.background_border)

        # XXX seperate drawing the keys and the fonts to avoid
        # XXX reloading the texture each time

        # first draw keys without the font
        key_normal = resource_find(self.key_background_disabled_normal
                                   if self.disabled else
                                   self.key_background_normal)
        texture = Image(key_normal, mipmap=True).texture
        with self.background_key_layer:
            for line_nb in range(1, layout_rows + 1):
                for pos, size in layout_geometry['LINE_%d' % line_nb]:
                        BorderImage(texture=texture, pos=pos, size=size,
                                    border=self.key_border)

        # then draw the text
        # calculate font_size
        font_size = int(w) / 30 # 46
        # draw
        for line_nb in range(1, layout_rows + 1):
            key_nb = 0
            for pos, size in layout_geometry['LINE_%d' % line_nb]:
                # retrieve the relative text
                text = layout[layout_mode + '_' + str(line_nb)][key_nb][0]
                l = Label(text=text, font_size=font_size, pos=pos, size=size,
                          font_name=self.font_name)
                self.add_widget(l)
                key_nb += 1


    def __check_orientation(self, *args):
        win = self.get_root_window()
        if win:
            orientation = 'portrait' if win.size[0] < win.size[1] else 'landscape'
            Clock.schedule_once(functools.partial(Keyboard.Resize, orientation, win.size), 0)
            #self.bubble = Bubble()
            #from kivy.uix.textinput import TextInput
            #ti = TextInput()
            #def text_changed(text, *a):
            #    ti.text = text
            #self.target.bind(on_text=text_changed)
            #self.bubble.add_widget(ti)
            #self.target.add_widget(self.bubble)

    @classmethod
    def Resize(cls, orientation, size, *args):
        if cls.__instance_ref:
            keyboard = cls.__instance_ref()
            if keyboard:
                keyboard.height = 500 if orientation == 'portrait' else 200
                Logger.info('Keyboard.Resize {} {} => {}x{}'.format(orientation, size, keyboard.width, keyboard.height))
                keyboard.setup_mode()
                keyboard.refresh(True)

    @classmethod
    def get_instance(cls):
        try: return cls.__instance_ref()
        except: return None
