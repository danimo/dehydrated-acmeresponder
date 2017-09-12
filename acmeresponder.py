#!/usr/bin/python3
#
# Author: Daniel Molkentin <daniel.molkentin@suse.de>
# Source: https://github.com/danimo/acmeresponder
#
# This script is licensed under The MIT License (see LICENSE for more information).

import os
import socket
import threading
import logging

from optparse import OptionParser
from urllib.parse import quote_plus
from http.server import SimpleHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s [%(threadName)s@%(asctime)s]")

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    pass

class SocketInheritingHTTPServer(ThreadedHTTPServer):
    """A HttpServer subclass that takes over an inherited socket from systemd"""
    def __init__(self, address_info, handler, fd, bind_and_activate=True):
        ThreadedHTTPServer.__init__(self, address_info, handler, bind_and_activate=False)
        self.socket = socket.fromfd(fd, self.address_family, self.socket_type)
        if bind_and_activate:
            # NOTE: systemd provides ready-bound sockets, so we only need to activate:
            self.server_activate()
def main():
    parser = OptionParser("usage: %prog [OPTIONS]")
    parser.add_option("-p", "--port", default=8080, type="int", help="TCP port to use [default: %default]")

    opts, args = parser.parse_args()
    port = opts.port

    if os.environ.get('LISTEN_PID', None) == str(os.getpid()):
        SYSTEMD_FIRST_SOCKET_FD = 3
        server_args = [('localhost', int(port)), SimpleHTTPRequestHandler]
        httpserv = SocketInheritingHTTPServer(*server_args, fd=SYSTEMD_FIRST_SOCKET_FD)
        logging.info('socket activated mode: started on socket fd %s' % (SYSTEMD_FIRST_SOCKET_FD,))
    else:
        httpserv = ThreadedHTTPServer(*server_args)
        logging.info('standalone mode: port %s' % (port,))
    httpserv.serve_forever()

if __name__ == "__main__":
    main()


