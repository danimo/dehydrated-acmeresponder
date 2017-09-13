PREFIX=/usr/local

install:
	install -m 755 acmeresponder.py $(DESTDIR)$(PREFIX)/sbin/acmeresponder
	install -m 644 acmeresponder.service $(DESTDIR)/etc/systemd/system/acmeresponder.service 
	install -m 644 acmeresponder.socket  $(DESTDIR)/etc/systemd/system/acmeresponder.socket

enable: install
	systemctl daemon-reload
	systemctl enable acmeresponder.socket

.PHONY=install
