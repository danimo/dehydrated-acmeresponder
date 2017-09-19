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
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DEFAULT_CHALLENGE_DIR = "/var/lib/acme-challenge"
CHALLENGEPATH = "/.well-known/acme-challenge"

class AcmeHTTPRequestHandler(BaseHTTPRequestHandler):
    """ A HTTP request handler that will only serve acme requests"""

    def get_challengedir_file(self, filename):
        challenge_dir = os.getenv("WELLKNOWN")
        if challenge_dir is None or challenge_dir == '':
            challenge_dir = DEFAULT_CHALLENGE_DIR
        return challenge_dir + '/' + filename

    def do_HEAD(self):
            self.handle_request(False)

    def do_GET(self):
            self.handle_request(True)

    def handle_request(self, write_file):
        normpath = os.path.normpath(self.path)
        if normpath.startswith(CHALLENGEPATH):
            normpath = normpath.replace(CHALLENGEPATH, '')
            logging.info('normpath %s' % (normpath,))
            if (os.path.exists(self.get_challengedir_file(normpath))):
                try:
                    with open(self.get_challengedir_file(normpath), 'rb') as r:
                        response = r.read()
                        length = len(response)
                        self.send_response(200, 'OK')
                        self.send_header('Content-type', 'text/plain')
                        self.send_header('Content-Length', length)
                        self.log_request(200, length)
                        self.end_headers()
                        if write_file == True:
                            self.wfile.write(response)
                except IOError as err:
                        self.send_response(403, 'Forbidden')
                        self.log_error('Error:', err)
                except:
                        self.send_response(500, 'Internal Server Error')
                        self.log_error('Error:')
                return

        self.send_response(404, 'Not Found')
        self.log_request(404)
        self.end_headers()

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
    server_args = [('localhost', int(port)), AcmeHTTPRequestHandler]

    if os.environ.get('LISTEN_PID', None) == str(os.getpid()):
        SYSTEMD_FIRST_SOCKET_FD = 3
        httpserv = SocketInheritingHTTPServer(*server_args, fd=SYSTEMD_FIRST_SOCKET_FD)
        logging.info('socket activated mode: started on socket fd %s' % (SYSTEMD_FIRST_SOCKET_FD,))
    else:
        httpserv = ThreadedHTTPServer(*server_args)
        logging.info('standalone mode: port %s' % (port,))
    httpserv.serve_forever()

if __name__ == "__main__":
    main()


