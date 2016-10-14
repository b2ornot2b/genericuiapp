from __future__ import print_function

from kivy.clock import Clock
from kivy.app import App

import os.path
from util import get_sdcard_path
import tarfile
from zipfile import ZipFile

from androidtoast import toast

import sys
import urllib2
import io
from ConfigParser import SafeConfigParser as ConfigParser


def update_from_sdcard(filename=None, fileobj=None):
    filename = 'gupdate.pk' if filename is None else filename
    path = os.path.join(get_sdcard_path(), filename)
    print('update_from_sdcard: {}'.format(path))
    tar = tarfile.open(path, fileobj=fileobj)
    update_version = int(tar.extractfile('version.txt').read().strip())
    print('update_version: {}'.format(update_version))

    version = int(open('version.txt').read().strip())
    print('       version: {}'.format(version))
    if update_version > version:
        print('extracting update...')
        tar.extractall()
        print('extracting update... done.')
        toast("App updated to version {}. Restarting...".format(update_version), True)
        Clock.schedule_once(restart, 5)

def update():
    try:
        config = ConfigParser()
        config.read('app.ini')
        url = config.get('updater', 'url')
        print("update url {}".format(url))
        fd = urllib2.urlopen(url)
        update_from_sdcard(fileobj=io.BytesIO(fd.read()))
    except:
        import traceback
        traceback.print_exc()
        update_from_sdcard()

def restart(*args):
    print('restart')
    App.get_running_app().stop()
    #sys.exit()
