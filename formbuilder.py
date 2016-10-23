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
from kivytoast import toast

import sqlite3
import plyer

from os.path import join, dirname, basename, exists
import datetime
import json
import functools
import collections
import traceback
import re
import csv
import time
import os
import shutil
from pprint import pprint

class FormBuilder(Screen):
    StorageDirectory = 'ascan'
    @classmethod
    def storage_path(cls, *paths, **kwargs):
        filename = kwargs.get('filename')
        path = join(get_sdcard_path(), cls.StorageDirectory, *paths)
        try: os.makedirs(path)
        except: pass
        if filename:
            path = join(path, filename)
        return path

    @classmethod
    def load_fieldspec(cls):
        try: return cls.csv2json()
        except:
            exc = traceback.format_exc()
            print(exc)

    def __init__(self, sm, *a, **k):
        formbuilder_csv = k.pop('formbuilder_csv', None)
        if formbuilder_csv:
            shutil.copyfileobj(open(formbuilder_csv), open(self.storage_path(filename='formbuilder.csv'), 'w'))
        self.fieldspec_json_filename = FormBuilder.load_fieldspec()

        super(FormBuilder, self).__init__(*a, **k)
        self.last_back_at = time.time()
        self.forms = {}
        self.pretty_fields = {}
        self.screen_manager = sm
        self.reload()
        self.barcode_widgets = [ None, None ]
        self.barcode_fields = []
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
        n = time.localtime()
        csvpath = self.storage_path('csv', filename='entries-{}{}{}-{}{}.csv'.format(n.tm_year, n.tm_mon, n.tm_mday, n.tm_hour, n.tm_min))
        Logger.info('open_database {}'.format(csvpath))
        pretty_fields = json.load(open(self.storage_path(filename='fields.json')))
        fields = sorted(pretty_fields.values())
        fields.insert(0, 'Barcode')
        fields.append('Timestamp')
        pretty_fields['barcode'] = 'Barcode'
        pretty_fields['timestamp'] = 'Timestamp'
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
        toast("You must restart the app for the keyboard setting to take effect")

    def check_for_updates(self, *args):
        Logger.info('check_for_updates')
        from util import run_on_new_thread
        from updater import update
        run_on_new_thread(update)

    def reload(self):
        self.config = json.load(open(self.fieldspec_json_filename), object_pairs_hook=collections.OrderedDict)

    def main_btn_pressed(self, form, *args):
        Logger.info('main_btn_pressed {} {}'.format(form, args))
        Clock.schedule_once(functools.partial(self.create_form, form), 0)

    def create_form(self, form, *args):
        Logger.info('create_form {} {}'.format(form, args))
        if form in self.forms:
            return self.set_form(form)

        screen = Screen(name=form, size_hint=(1,1))
        accordion = Accordion(orientation="vertical", size_hint=(1,1))
        wprev = None
        for tab in self.config[form]:
            item = AccordionItem(title=tab,
                              background_normal="atlas://data/images/defaulttheme/modalview-background")
            wprev = self.create_form_entries(item, form, tab, wprev)
            accordion.add_widget(item)
        try: json.dump(self.pretty_fields, open(self.storage_path(filename='fields.json'), 'w'))
        except: pass
            
        barcode_item = AccordionItem(title="Barcode",
                              background_normal="atlas://data/images/defaulttheme/modalview-background")
        self.create_barcode_widget(barcode_item)
        accordion.add_widget(barcode_item)
        screen.add_widget(accordion)
        self.screen_manager.add_widget(screen)
        self.forms[form] = screen
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
        self.barcode_widgets[0].bind(on_text_done=self.on_manual_barcode_text_done)

        self.clear_btn = Button(text="Clear", size_hint=(1,1,))
        self.clear_btn.bind(on_press=self.clear_record)
        layout.add_widget(self.clear_btn)

        self.save_btn = Button(text="Save", size_hint=(1,1,))
        self.save_btn.bind(on_press=self.save_record)
        layout.add_widget(self.save_btn)

        root.add_widget(layout)

    def on_manual_barcode_text_done(self, ti, value, *a):
        Logger.info('on_manual_barcode_text_done {} {} {}'.format(ti, value, a))
        self.barcode_changed(0, ti, False)

    def save_record(self, *args):
        Logger.info('save_record')
        record = self.get_record_dict()
        record['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

        self.populate_autocomplete_from_data(record)
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
        dbpath = self.storage_path(filename='entries.db')
        Logger.info('open_database {}'.format(dbpath))
        self.conn = sqlite3.connect(dbpath)
        c = self.conn.cursor()
        c.execute('''create table if not exists entry (idx INTEGER PRIMARY KEY AUTOINCREMENT, start UNIQUE, stop, data)''')
        c.execute('''create table if not exists autocomplete (field, word, count integer default 0, PRIMARY KEY(field, word))''');
        self.conn.commit()

        c = self.conn.cursor()
        count = 0
        for row in c.execute('''select count(*) from autocomplete'''):
            count = row[0]
        if count is 0:
            self.populate_autocomplete_from_entrytable()

    def populate_autocomplete_from_entrytable(self):
        Logger.info('populate_autocomplete_from_entry')
        c = self.conn.cursor()
        cins = self.conn.cursor()
        for row in c.execute('''select data from entry'''):
            try: data = json.loads(row[0])
            except: continue
            self.populate_autocomplete_from_data(data, cins)
        self.conn.commit()
       
    def populate_autocomplete_from_data(self, data, cursor=None):
        cursor = self.conn.cursor() if cursor is None else cursor
        for k, v in data.items():
            try:
                words = v.split()
                kw = [ (k, w.upper()) for w in words ]
                cursor.executemany('''insert or ignore into autocomplete(field, word) values (?,?)''', kw)
                cursor.executemany('''update autocomplete set count=count+1 where field=? and word=?''', kw)
            except:
                traceback.print_exc()

    def clear_record(self, *args):
        Logger.info('clear_record')
        for i in range(2):
            try: self.barcode_widgets[i].text = ''
            except: pass
            try: self.barcode_widgets[i].popup_input.text = ''
            except: pass
        
        for form in self.config:
            for tab in self.config[form]:
                for field in self.config[form][tab]:
                    entry = self.config[form][tab][field]
                    if entry["lable_widget"].state != 'down':
                        try: entry["widget"].text = ''
                        except: pass
                        try: entry["widget"].popup_input.text=""
                        except: pass
                    if entry["type"].lower() == "camera":
                        entry["widget"].text = ""
                        entry["widget"].background_normal = ""
                        
                        
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
                        Logger.info("set {} => {} : {}".format(entry["reckey"], value, entry["widget"]))
                    except KeyError:
                        value = ""
                    entry["widget"].text = value

    BarcodePrefixes = set([ 'HGSL', 'ISPL', 'ISPD' ])
    def on_barcode_scanned(self, barcode):
        Logger.info('FormBuilder.on_barcode_scanned {}'.format(barcode))
        try:
            prefix = barcode[:4].upper()
        except:
            prefix = None

        if prefix not in self.BarcodePrefixes:
            for entry in self.barcode_fields:
                entry["widget"].text = barcode
            return
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
        try: saved_record = json.load(open(self.storage_path(filename='lockedfields.json')))
        except: saved_record = {}
        def xform(k):
            return u''.join([ c for c in k if c.isalnum() ])
        for field in self.config[form][tab]:
            entry = self.config[form][tab][field]
            entry['reckey'] = xform('{}{}'.format(tab, field))
            self.pretty_fields[entry['reckey']] = '{} {}'.format(tab, field)
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
            entry_type = entry["type"].lower()
            if entry_type in ("text", "barcode"):
                e = PopupTextInput(titlewidget=lbl, size_hint=(1, 1), wprev=wprev, conn=self.conn, field=entry['reckey'])
                if wprev:
                    wprev.set_wnext(e)
                wprev = e
                e.bind(text=functools.partial(self.data_changed, form, tab, field, entry))
            elif entry_type == "dropdown":
                e = Spinner(size_hint=(1, None), values=entry["values"])
                e.bind(text=functools.partial(self.data_changed, form, tab, field, entry))
            elif entry_type == "camera":
                e = Button(text="", on_press=functools.partial(self.capture_camera, form, tab, field, entry))

            layout.add_widget(lbl)
            layout.add_widget(e)
            entry["root"] = root
            entry["root_title"] = tab
            entry["lable_widget"] = lbl
            entry["widget"] = e
            if entry_type == "barcode":
                self.barcode_fields.append(entry)
            if saved_text:
                e.text = saved_text
                e.disabled = True
        root.add_widget(layout)
        # return wprev

    def capture_camera(self, form, tab, field, entry, *args):
        Logger.info("capture_camera {} {}".format(tab, field))
        try: barcode = self.barcode_widgets[0].text.strip()
        except: barcode = ''
        if len(barcode) == 0:
            plyer.vibrator.vibrate(0.1)
            toast("Barcode is empty.")
            return
        filename = self.storage_path('rawimgs', filename="camraw-{}.jpg".format(barcode))
        Logger.info('Image: {}'.format(filename))
        plyer.camera.take_picture(filename, functools.partial(self.on_picture_done, barcode, entry))

    def on_picture_done(self, barcode, entry, filename, *a):
        Logger.info('on_picture_done {} {}'.format(filename, entry))
        import Image
        im = Image.open(filename)
        Logger.info('image {} {} {}'.format(im.format, im.size, im.mode))
        # size = [ int(i) for i in entry["widget"].size ]
        #try: ratio = im.size[0]/float(im.size[1])
        #except: ratio = 1.
        #size = [ 640, int((480/im.size[1])*ratio) ]
        size = [ 640., None ]
        size[1] = size[0] * im.size[1] / im.size[0]
        size = map(int, size)
        Logger.info('resize {} => {}'.format(im.size, size))
        btn_im = im.resize(size)
        thumbfile = self.storage_path('imgs', filename='cam-{}.jpg'.format(barcode))
        btn_im.save(thumbfile)
        Logger.info("setting background {}".format(thumbfile))
        try: os.unlink(filename)
        except: pass
        entry["widget"].text = basename(thumbfile)
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
        texts = ( e["widget"].text for field,e in self.config[form][tab].items() if e.has_key("widget"))
        texts = ( t for t in texts if len(t) )
        texts = u' '.join(texts)
        entry["root"].title = u"{}: {}".format(entry["root_title"], texts)
            
    def locked_btn_pressed(self, form, tab, field, entry, *args):
        Logger.info('locked_btn_pressed {} {} {} {}'.format(form, tab, field, entry, args))
        Logger.info('widget {} {} {}'.format(entry["widget"], entry["widget"].disabled, entry["lable_widget"].state))
        entry["widget"].disabled = entry["lable_widget"].state == "down"
        if entry["widget"].disabled:
            record = self.get_record_dict(only_locked_fields=True)
            json.dump(record, open(self.storage_path(filename='lockedfields.json'), 'w'))

    @classmethod
    def csv2json(cls, filename=None, jsonfilename=None):
        Logger.info('formbuilder.load {}'.format(filename))
        if filename is None:
            filename = cls.storage_path(filename='formbuilder.csv')
            jsonfilename = cls.storage_path(filename='formbuilder.json')
            if not exists(filename):
                filename = 'formbuilder.csv'
                jsonfilename = 'formbuild.json'

        def xform(k):
            return u''.join([ c for c in k if c.isalnum() ])
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
        json.dump(forms, open(jsonfilename, 'w'),
                  sort_keys=False, indent=4, separators=(',', ':'))
        return jsonfilename
                    
if __name__ == '__main__':
    FormBuilder.load()
