from __future__ import print_function

from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.accordion import Accordion, AccordionItem
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton

from kivy.clock import Clock
from kivy.logger import Logger

from util import get_sdcard_path, android_share
from popuptextinput import PopupTextInput

import sqlite3
import plyer

from os.path import join, dirname
import json
import functools
import collections
import traceback
import re
import csv
import time
import os
from pprint import pprint

class FormBuilder(Screen):
    @classmethod
    def storage_path(cls, *a):
        path = join(get_sdcard_path(), 'ascan')
        try: os.mkdir(path)
        except: pass
        return path

    def __init__(self, sm, *a, **k):
        super(FormBuilder, self).__init__(*a, **k)
        self.last_back_at = time.time()
        self.pretty_fields = {}
        self.screen_manager = sm
        self.reload()
        self.barcode_widgets = [ None, None ]
        self.create_ui()
        Clock.schedule_once(self.open_database, 0)

    def on_back(self, *args):
        Logger.info('on_back {}'.format(args))

        now = time.time()
        if self.screen_manager.current == "home":
            return False
        else:
            Window.release_all_keyboards()
            if (now - self.last_back_at) < 1:
                self.screen_manager.current = "home"
        self.last_back_at = now
        return True

    def create_ui(self):
        screen = Screen(name="home")
        main_layout = BoxLayout(orientation='vertical', size_hint_y=None, padding=10)

        version = open('version.txt').read().strip()
        update_btn = Button(text="Check for updates\n ver {}".format(version), height=300, size_hint=(1, None), on_press=self.check_for_updates)
        main_layout.add_widget(update_btn)

        share_btn = Button(text="Share", height=300, size_hint=(1, None), on_press=self.share_data)
        main_layout.add_widget(share_btn)


        bl = BoxLayout(orientation="horizontal", height=300, size_hint=(1, None))
        from keyboard import get_keyboard_config
        softkeyboard_switch = Switch(active=(get_keyboard_config() == "system"))
        softkeyboard_switch.bind(active=self.softkeyboard_switch_changed)
        bl.add_widget(Label(text="Use system keyboard"))
        bl.add_widget(softkeyboard_switch)
        main_layout.add_widget(bl)

        for form in self.config:
            btn = Button(text=form, height=250, size_hint=(1, None), on_press=functools.partial(self.main_btn_pressed, form))
            main_layout.add_widget(btn)

        screen.add_widget(main_layout)
        self.screen_manager.add_widget(screen)
        self.screen_manager.current = "home"

    def share_data(self, *args):
        Logger.info('share_data')
        cursor = self.conn.cursor()
        print(cursor)

        n = time.localtime()
        csvpath = join(self.storage_path(), 'entries-{}{}{}-{}{}.csv'.format(n.tm_year, n.tm_mon, n.tm_mday, n.tm_hour, n.tm_min))
        Logger.info('open_database {}'.format(csvpath))
        pretty_fields = json.load(open('fields.json'))
        fields = sorted(pretty_fields.values())
        fields.insert(0, 'Barcode')
        pretty_fields['barcode'] = 'Barcode'
        with open(csvpath, 'w') as csvfd:
            writer = csv.DictWriter(csvfd, fields)
            writer.writeheader()
            for row in cursor.execute('''select idx, start, stop, data from entry order by idx'''):
                print(row)
                try: idx, start, stop, data = row[0], row[1], row[2], json.loads(row[3])
                except:
                    traceback.print_exc()
                    print('bad data')
                    continue
                for entry in self.get_rows(start, stop, data):
                    entry = { pretty_fields.get(k,None): v.encode('utf8') for k, v in entry.items() }
                    try: del entry[None]
                    except: pass
                    pprint(entry)
                    writer.writerow(entry)
        android_share(attachment=csvpath)
        
    def get_rows(self, start, stop, data):
        Logger.info('get_rows {} {} {}'.format(start, stop, len(data)))
        data["barcode"] = start
        if len(stop) == 0:
            yield data
            return
        try:
            istart = re.findall(r'\d+$', start)[0]
            p1 = start[:-len(istart)]
            istart = int(istart)

            istop = re.findall(r'\d+$', stop)[0]
            p2 = stop[:-len(istop)]
            istop = int(istop)
            assert(p1==p2)
        except:
            traceback.print_exc()
            yield data
            return
        print('irange: {} => {} ({})'.format(istart, istop, istop-istart+1))
        for i in range(istart, istop+1):
            barcode = "{}{}".format(p1, i)
            data["barcode"] = barcode
            yield data
 
    def softkeyboard_switch_changed(self, switch, value, *args):
        Logger.info("softkeyboard_switch_changed {} {} {}".format(switch, value, args))
        from keyboard import set_keyboard_config
        set_keyboard_config("system" if value else "dock")
        from kivytoast import toast
        toast("You must restart the app for the keyboard setting to take effect")

    def check_for_updates(self, *args):
        Logger.info('check_for_updates')
        from util import run_on_new_thread
        from updater import update
        run_on_new_thread(update)

    def reload(self):
        self.config = json.load(open('formbuilder.json'), object_pairs_hook=collections.OrderedDict)

    def main_btn_pressed(self, form, *args):
        Logger.info('main_btn_pressed {} {}'.format(form, args))
        Clock.schedule_once(functools.partial(self.create_form, form), 0)

    def create_form(self, form, *args):
        Logger.info('create_form {} {}'.format(form, args))
        screen = Screen(name=form, size_hint=(1,1))
        accordion = Accordion(orientation="vertical", size_hint=(1,1))
        wprev = None
        for tab in self.config[form]:
            item = AccordionItem(title=tab,
                              background_normal="atlas://data/images/defaulttheme/modalview-background")
            wprev = self.create_form_entries(item, form, tab, wprev)
            accordion.add_widget(item)
        try: json.dump(self.pretty_fields, open('fields.json', 'w'))
        except: pass
            
        barcode_item = AccordionItem(title="Barcode",
                              background_normal="atlas://data/images/defaulttheme/modalview-background")
        self.create_barcode_widget(barcode_item)
        accordion.add_widget(barcode_item)
        screen.add_widget(accordion)
        self.screen_manager.add_widget(screen)
        Clock.schedule_once(functools.partial(self.set_form, form), 0)

    def set_form(self, form, *args):
        self.screen_manager.current = form

    def create_barcode_widget(self, root):
        Logger.info('create_barcode_widget')
        layout = GridLayout(cols=2, size_hint=(1,1))
        for i, text in enumerate([ 'Barcode start', 'Barcode stop' ]):
            lbl = Label(text=text)
            layout.add_widget(lbl)
            self.barcode_widgets[i] = e = PopupTextInput(text="", titlewidget=lbl, size_hint=(1, 1))
            #e.bind(focus=functools.partial(self.barcode_changed, i))
            layout.add_widget(e)

        self.clear_btn = Button(text="Clear", size_hint=(1,1,))
        self.clear_btn.bind(on_press=self.clear_record)
        layout.add_widget(self.clear_btn)

        self.save_btn = Button(text="Save", size_hint=(1,1,))
        self.save_btn.bind(on_press=self.save_record)
        layout.add_widget(self.save_btn)

        root.add_widget(layout)

    def save_record(self, *args):
        Logger.info('save_record')
        record = self.get_record_dict()
        start = self.barcode_widgets[0].text.strip()
        stop = self.barcode_widgets[1].text.strip()
        import csv
        if len(start) is 0:
            plyer.vibrator.vibrate(0.1)
            return

        c = self.conn.cursor()
        c.execute('''insert or replace into entry (start, stop, data) values (?,?,?)''',
                  (start, stop, json.dumps(record)))
        self.conn.commit()
        self.clear_record()
        plyer.vibrator.vibrate(.4)

    def get_record_dict(self, only_locked_fields=False):
        record = {}
        for form in self.config: # TODO: Store form in record
            for tab in self.config[form]:
                for field in self.config[form][tab]:
                    try:
                        entry = self.config[form][tab][field]
                        if only_locked_fields and entry["widget"].disabled is False:
                            continue
                        v = entry["widget"].text.strip()
                        if len(v):
                            record[entry["reckey"]] = v
                    except:
                        pass
        for i, k in enumerate(['barcode_start', 'barcode_stop']):
            if self.barcode_widgets[i] is None:
                continue
            if len(self.barcode_widgets[i].text.strip()):
                v = self.barcode_widgets[i].text.strip()
                record[k] = v
        pprint(record)
        return record

    def open_database(self, *args):
        dbpath = join(self.storage_path(), 'entries.db')
        Logger.info('open_database {}'.format(dbpath))
        self.conn = sqlite3.connect(dbpath)
        c = self.conn.cursor()
        c.execute('''create table if not exists entry (idx INTEGER PRIMARY KEY AUTOINCREMENT, start UNIQUE, stop, data)''')
        self.conn.commit()

    def clear_record(self, *args):
        Logger.info('clear_record')
        for i in range(2):
            self.barcode_widgets[i].text = ''
        
        for form in self.config:
            for tab in self.config[form]:
                for field in self.config[form][tab]:
                    entry = self.config[form][tab][field]
                    if entry["lable_widget"].state != 'down':
                        entry["widget"].text = ''
        return False

    def barcode_changed(self, i, ti, value):
        Logger.info('barcode_changed {} {} {}'.format(i, ti, value))
        if not (value is False and i==0):
            return
        value = ti.text.strip()
        Logger.info('searching {}...'.format(value))
        cursor = self.conn.cursor()
        for row in cursor.execute('''select start, stop, data from entry where start=?''',
                       (value,)):
            Logger.info('row={}'.format(row))
            try: start, stop, data = row[0], row[1], json.loads(row[2])
            except: continue
            Logger.info('found {} {}'.format(start, stop))
            self.update_fields(data)

    def update_fields(self, data):
        Logger.info("update_fields {}".format(data))
        for form in self.config:
            for tab in self.config[form]:
                for field in self.config[form][tab]:
                    entry = self.config[form][tab][field]
                    try:
                        value = data[entry["reckey"]]
                        Logger.info("set {} => {}".format(entry["reckey"], value))
                    except KeyError:
                        value = ""
                    entry["widget"].text = value

    def on_barcode_scanned(self, barcode):
        Logger.info('FormBuilder.on_barcode_scanned {}'.format(barcode))
        for i in range(2):
            if self.barcode_widgets[i] is None:
                continue
            if len(self.barcode_widgets[i].text.strip()) == 0:
                self.barcode_widgets[i].text = barcode
                self.barcode_changed(i, self.barcode_widgets[i], False)
                return
        
    def create_form_entries(self, root, form, tab, wprev=None):
        Logger.info('create_form_entries {} {}'.format(form, tab))
        layout = GridLayout(cols=2, size_hint=(1,1))
        try: saved_record = json.load(open('lockedfields.json'))
        except: saved_record = {}
        def xform(k):
            return ''.join([ c for c in k if c.isalnum() ])
        for field in self.config[form][tab]:
            entry = self.config[form][tab][field]
            entry['reckey'] = xform('{}{}'.format(tab, field))
            self.pretty_fields[entry['reckey']] = field
            try: saved_text = saved_record[entry['reckey']]
            except KeyError: saved_text = None
            if True: # entry["lock"]:
                lbl = ToggleButton(text=field,
                                   state=('normal' if saved_text is None else 'down'),
                                   background_normal="atlas://data/images/defaulttheme/button_pressed",
                                   background_down="atlas://data/images/defaulttheme/button")
                lbl.bind(state=functools.partial(self.locked_btn_pressed, form, tab, field, entry))
            else:
                lbl = Label(text=field)
            e = Label()
            if entry["type"].lower() == "text":
                e = PopupTextInput(titlewidget=lbl, size_hint=(1, 1), wprev=wprev)
                if wprev:
                    wprev.set_wnext(e)
                wprev = e
                e.bind(text=functools.partial(self.data_changed, form, tab, field, entry))
            elif entry["type"].lower() == "dropdown":
                e = Spinner(size_hint=(1, None), values=entry["values"])
                e.bind(text=functools.partial(self.data_changed, form, tab, field, entry))
            elif entry["type"].lower() == "camera":
                e = Button(text="Camera", on_press=functools.partial(self.capture_camera, form, tab, field, entry))
            layout.add_widget(lbl)
            layout.add_widget(e)
            entry["root"] = root
            entry["root_title"] = root.title
            entry["lable_widget"] = lbl
            entry["widget"] = e
            if saved_text:
                e.text = saved_text
                e.disabled = True
        root.add_widget(layout)
        # return wprev

    def capture_camera(self, form, tab, field, entry, *args):
        Logger.info("capture_camera {} {}".format(tab, field))
        gimgs = join(self.storage_path(), 'gimgs')
        try: os.mkdir(gimgs)
        except: pass
        filename = join(gimgs, "camera.jpg")
        Logger.info('Image: {}'.format(filename))
        plyer.camera.take_picture(filename, functools.partial(self.on_picture_done, entry))

    def on_picture_done(self, entry, filename, *a):
        Logger.info('on_picture_done {} {}'.format(filename, entry))
        import Image
        im = Image.open(filename)
        Logger.info('image {} {} {}'.format(im.format, im.size, im.mode))
        size = [ int(i) for i in entry["widget"].size ]
        Logger.info('widget size {}'.format(size))
        btn_im = im.resize(size)
        thumbfile = join(dirname(filename), 'camera-thumb.jpg')
        btn_im.save(thumbfile)
        Logger.info("setting background {}".format(thumbfile))
        def do_later1(_t1, *a):
            entry["widget"].background_normal  = ""
            def do_later2(_t2, *a):
                entry["widget"].background_normal  = _t2
            Clock.schedule_once(functools.partial(do_later2, _t1), 0)
        Clock.schedule_once(functools.partial(do_later1, thumbfile), 0)

    def data_changed(self, form, tab, field, entry, *args):
        Logger.info("data_changed {} {}".format(tab, field))
        self.do_data_changed(form, tab, field, entry, *args)

    def do_data_changed(self, form, tab, field, entry, *args):
        #Logger.info("do_data_changed {} {} {} {} {}".format(form, tab, field, entry, args))
        texts = ( e["widget"].text for field,e in self.config[form][tab].items() if e.has_key("widget"))
        texts = ( t for t in texts if len(t) )
        texts = u' '.join(texts)
        entry["root"].title = u"{}: {}".format(entry["root_title"], texts)
            
    def locked_btn_pressed(self, form, tab, field, entry, *args):
        Logger.info('locked_btn_pressed {} {} {} {}'.format(form, tab, field, entry, args))
        entry["widget"].disabled = entry["lable_widget"].state == "down"
        if entry["widget"].disabled:
            record = self.get_record_dict(only_locked_fields=True)
            json.dump(record, open('lockedfields.json', 'w'))

    @classmethod
    def load(cls, filename=None):
        if filename is None:
            filename = 'formbuilder.csv'

        def xform(k):
            return ''.join([ c for c in k if c.isalnum() ])
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
