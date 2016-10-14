SHELL=/bin/bash
APK := GenericUI-0.1-debug.apk
UPDATEPK := gupdate.pk

SRCS := $(wildcard *.py)
TARGETS := bin/$(APK) bin/$(UPDATEPK)

VERSION := $(shell cat version.txt)

.PHONY: all
all: $(TARGETS)

bin/GenericUI-0.1-debug.apk:  buildozer.spec version.txt $(SRCS)
	buildozer android debug

bin/gupdate.pk:	version.txt $(SRCS)
	tar cvf $@ version.txt $(SRCS) b2kbd.json

.PHONY: copy2host copyapk2host copypk2host bumpversion installapk installpk

copy2host: copyapk2host copypk2host

copyapk2host: bin/$(APK)
	sudo cp -v $^ /media/sf_tmp/

copypk2host: bin/$(UPDATEPK)
	sudo cp -v $^ /media/sf_tmp/


bumpversion:
	 echo $$(( $(VERSION) + 1 )) > version.txt

installapk: copy2host
	ssh b2@192.168.1.13 "/home/b2/Android/Sdk/platform-tools/adb install -r  /tmp/$(APK)"

installpk: copy2host
	ssh b2@192.168.1.13 "/home/b2/Android/Sdk/platform-tools/adb push /tmp/$(UPDATEPK) /mnt/sdcard/$(UPDATEPK)"

.PHONY: clean
clean:
	rm -f $(TARGETS)
