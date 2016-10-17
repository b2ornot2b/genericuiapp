from __future__ import print_function

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton

from kivy.clock import Clock
from kivy.logger import Logger

import json
import functools
import collections
from pprint import pprint

class FormBuilder(Screen):
    def __init__(self, sm, *a, **k):
        super(FormBuilder, self).__init__(*a, **k)
        self.screen_manager = sm
        self.reload()
        self.create_ui()

    def create_ui(self):
        main_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=10)
        for form in self.config:
            btn = Button(text=form, size_hint=(1, None), on_press=functools.partial(self.main_btn_pressed, form))
                
            main_layout.add_widget(btn)
        self.add_widget(main_layout)

    def reload(self):
        self.config = json.load(open('formbuilder.json'), object_pairs_hook=collections.OrderedDict)

    def main_btn_pressed(self, form, *args):
        Logger.info('main_btn_pressed {} {}'.format(form, args))
        Clock.schedule_once(functools.partial(self.create_form, form), 0)

    def create_form(self, form, *args):
        Logger.info('create_form {} {}'.format(form, args))
        screen = Screen(name=form, size_hint=(1,1))
        accordion = Accordion(orientation="vertical", size_hint=(1,1))
        for tab in self.config[form]:
            item = AccordionItem(title=tab)
            self.create_form_entries(item, form, tab)
            accordion.add_widget(item)
            
        barcode_item = AccordionItem(title="Barcode")
        self.create_barcode_widget(barcode_item)
        accordion.add_widget(barcode_item)
        screen.add_widget(accordion)
        self.screen_manager.add_widget(screen)
        Clock.schedule_once(functools.partial(self.set_form, form), 0)

    def set_form(self, form, *args):
        self.screen_manager.current = form

    def create_barcode_widget(self, root):
        Logger.info('create_barcode_widget')
        self.barcode_widget_lbl = lbl = Label(text="")
        root.add_widget(lbl)

    def on_barcode_scanned(self, barcode):
        Logger.info('FormBuilder.on_barcode_scanned {}'.format(barcode))
        self.barcode_widget_lbl.text = barcode
        
    def create_form_entries(self, root, form, tab):
        Logger.info('create_form_entries {} {}'.format(form, tab))
        layout = GridLayout(cols=2, size_hint=(1,1))
        for field in self.config[form][tab]:
            entry = self.config[form][tab][field]
            if entry["lock"]:
                lbl = ToggleButton(text=field)
                lbl.bind(state=functools.partial(self.locked_btn_pressed, form, tab, field, entry))
            else:
                lbl = Label(text=field)
            e = Label()
            if entry["type"].lower() == "text":
                e = TextInput(size_hint=(1, None))
                e.bind(text=functools.partial(self.data_changed, form, tab, field, entry))
            elif entry["type"].lower() == "dropdown":
                e = Spinner(size_hint=(1, None), values=entry["values"])
                e.bind(text=functools.partial(self.data_changed, form, tab, field, entry))
            elif entry["type"].lower() == "camera":
                e = Button(text="Camera")
            layout.add_widget(lbl)
            layout.add_widget(e)
            entry["root"] = root
            entry["root_title"] = root.title
            entry["lable_widget"] = lbl
            entry["widget"] = e
        root.add_widget(layout)

    def data_changed(self, form, tab, field, entry, *args):
        Logger.info("data_changed {} {}".format(entry, args))

        
        texts = [ e["widget"].text for field,e in self.config[form][tab].items()]
        Logger.info("texts: {}".format(texts))
        texts = [ t for t in texts if len(t) ]
        texts = ' '.join(texts)
        entry["root"].title = "{}: {}".format(entry["root_title"], texts)
            
        #for w in widgets:
        #    Logger.info("DATA: {}".format(w))
        #    try: Logger.info("DATA TEXT: {}".format(w.text))
        #    except:
        #        import traceback
        #        traceback.print_exc()
            

    def locked_btn_pressed(self, form, tab, field, entry, *args):
        Logger.info('locked_btn_pressed {} {} {} {}'.format(form, tab, field, entry, args))
        entry["widget"].disabled = entry["lable_widget"].state == "down"

    @classmethod
    def load(cls, filename=None):
        if filename is None:
            filename = 'formbuilder.csv'

        with open(filename) as csvfile:
            import csv
            fb = csv.reader(csvfile)
            forms = collections.OrderedDict()
            current = None
            headers = [ v.strip() for v in fb.next() ]
            for line in fb:
                line = [ v.strip() for v in line ]
                if len(line[0]):
                    current = forms[line[0]] = collections.OrderedDict()
                if len(line[1]):
                    tab = current[line[1]] = collections.OrderedDict()
                if len(line[2]) == 0:
                    continue
                
                # field
                field = tab[line[2]] = {"type": line[3] }
                field["lock"] = line[4].lower().startswith("y")
                field["comments"] = line[5]
                field["values"] = [ v for v in line[6:] if len(v) ]
                field["others"] = "Others" in field["values"]

                pprint(forms)
        json.dump(forms, open('formbuilder.json', 'w'),
                  sort_keys=False, indent=4, separators=(',', ':'))
                    
if __name__ == '__main__':
    FormBuilder.load()
