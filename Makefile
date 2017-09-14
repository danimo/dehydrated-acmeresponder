PREFIX=/usr/local
UNITDIR=/etc/systemd/system

install:
	install -m 755 acmeresponder.py $(DESTDIR)$(PREFIX)/sbin/acmeresponder
	install -m 644 acmeresponder.service $(DESTDIR)$(UNITDIR)/acmeresponder.service 
	install -m 644 acmeresponder.socket  $(DESTDIR)$(UNITDIR)/acmeresponder.socket

.PHONY=install
