SHELL=/bin/bash
APK := NiftyForms-1.0-debug.apk
UPDATEPK := gupdate.pk

SRCS := $(wildcard *.py)
TARGETS := bin/$(APK) bin/$(UPDATEPK)


.PHONY: all
all: $(TARGETS)

bin/GenericUI-0.1-debug.apk:  buildozer.spec version.txt $(SRCS)
	-mkdir bin
	buildozer android debug

bin/gupdate.pk:	version.txt $(SRCS)
	-mkdir bin
	tar cvf $@ version.txt $(SRCS) *.ini *.json *.csv

.PHONY: copy2host copyapk2host copypk2host bumpversion installapk installpk

copy2host: copyapk2host copypk2host

copyapk2host: bin/$(APK)
	sudo cp -v $^ /media/sf_tmp/

copypk2host: bin/$(UPDATEPK)
	sudo cp -v $^ /media/sf_tmp/


bumpversion:
	echo "Current Version: $$(cat version.txt)"
	echo $$(( $$(cat version.txt) + 1 )) > version.txt
	echo "Bumped  Version: $$(cat version.txt)"

installapk: copyapk2host
	ssh b2@192.168.1.13 "/home/b2/Android/Sdk/platform-tools/adb install -r  /tmp/$(APK)"

installpk: copypk2host
	ssh b2@192.168.1.13 "/home/b2/Android/Sdk/platform-tools/adb push /tmp/$(UPDATEPK) /mnt/sdcard/$(UPDATEPK)"

.PHONY: clean
clean:
	rm -f $(TARGETS)
