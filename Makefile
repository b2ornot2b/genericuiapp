bin/GenericUI-0.1-debug.apk:  buildozer.spec main.py
	buildozer android debug
	sudo cp -v bin/GenericUI-0.1-debug.apk /media/sf_tmp/
	ssh b2@192.168.1.13 "/home/b2/Android/Sdk/platform-tools/adb install -r  /tmp/GenericUI-0.1-debug.apk"

.PHONY: clean
clean:
	rm -f bin/GenericUI-0.1-debug.apk
