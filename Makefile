

DEB_FILE = dist/svnnotify.deb
DIST_DEB = dist/debian

all:

clean:
	rm -R dist

init:
	mkdir dist

dist-deb: $(DEB_FILE)

$(DEB_FILE):
	mkdir -p $(DIST_DEB)
	mkdir -p DEBIAN $(DIST_DEB)/DEBIAN
	install DEBIAN/control $(DIST_DEB)/DEBIAN
	install -m 0755 DEBIAN/postinst $(DIST_DEB)/DEBIAN/postinst
	install -m 0755 DEBIAN/prerm $(DIST_DEB)/DEBIAN/prerm
	install -D svnnotify.py $(DIST_DEB)/usr/share/svnnotify/svnnotify.py
	cd $(DIST_DEB)
	md5sum `find $(DIST_DEB) -type f | grep -v '^[.]/DEBIAN/'` > $(DIST_DEB)/DEBIAN/md5sums
	
	cd ../..
	fakeroot dpkg-deb -b $(DIST_DEB) $(DEB_FILE)

	
install-deb: $(DEB_FILE)
	sudo dpkg -i $(DEB_FILE)

dist-rpm:
