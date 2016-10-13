SRCS := $(wildcard *.py)
TARGETS := bin/GenericUI-0.1-debug.apk bin/gupdate.pk


.PHONY: all
all: $(TARGETS)

bin/GenericUI-0.1-debug.apk:  buildozer.spec version.txt $(SRCS)
	buildozer android debug
	sudo cp -v bin/GenericUI-0.1-debug.apk /media/sf_tmp/
	ssh b2@192.168.1.13 "/home/b2/Android/Sdk/platform-tools/adb install -r  /tmp/GenericUI-0.1-debug.apk"

bin/gupdate.pk:	version.txt $(SRCS)
	tar cvf $@ version.txt $(SRCS) b2kbd.json

.PHONY: clean
clean:
	rm -f $(TARGETS)
