from __future__ import print_function

from kivy.logger import Logger
from kivy.app import App

import threading
import traceback

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
        sdpath = Environment.getExternalStorageDirectory().getAbsolutePath()
    except Exception:
        print('get_sdcard_path: {}'.format(traceback.format_exc()))
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

