PREFIX=/usr/local

install:
	install -m 755 acmeresponder.py $(PREFIX)/sbin/acmeresponder
	install -m 644 acmeresponder.service /etc/systemd/system/acmeresponder.service 
	install -m 644 acmeresponder.socket  /etc/systemd/system/acmeresponder.socket

enable: install
	systemctl daemon-reload
	systemctl enable acmeresponder.socket

.PHONY=install
