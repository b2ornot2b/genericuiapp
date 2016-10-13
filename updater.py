from __future__ import print_function

from kivy.clock import Clock
from kivy.app import App

import os.path
from util import get_sdcard_path
import tarfile
from zipfile import ZipFile

from androidtoast import toast

import sys


def update_from_sdcard(filename=None):
    filename = 'gupdate.pk' if filename is None else filename
    path = os.path.join(get_sdcard_path(), filename)
    print('update_from_sdcard: {}'.format(path))
    tar = tarfile.open(path)
    update_version = int(tar.extractfile('version.txt').read().strip())
    print('update_version: {}'.format(update_version))

    version = int(open('version.txt').read().strip())
    print('       version: {}'.format(version))
    if update_version > version:
        print('extracting update...')
        tar.extractall()
        print('extracting update... done.')
        toast("App updated to version {}. Restarting...".format(version), True)
        Clock.schedule_once(restart, 5)

def restart(*args):
    print('restart')
    App.get_running_app().stop()
    #sys.exit()
