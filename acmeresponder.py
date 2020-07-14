#!/usr/bin/python3
#
# Author: Daniel Molkentin <daniel.molkentin@suse.de>
# Source: https://github.com/danimo/acmeresponder
#
# This script is licensed under The MIT License (see LICENSE for more information).

import os
import re
import socket
import threading
import logging

from optparse import OptionParser
from urllib.parse import quote_plus
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

DEFAULT_CHALLENGE_DIR = "/var/lib/acme-challenge"

class AcmeHTTPRequestHandler(BaseHTTPRequestHandler):
    """ A HTTP request handler that will only serve acme requests"""

    def get_challengedir(self):
        challenge_dir = os.getenv("WELLKNOWN")
        if challenge_dir is None or challenge_dir == '':
            challenge_dir = DEFAULT_CHALLENGE_DIR
        return challenge_dir

    def is_base64url(self, string):
        result = re.match("^([A-Fa-f0-9-_])*$", string)
        return result is not None

    def do_HEAD(self):
            self.handle_request(False)

    def do_GET(self):
            self.handle_request(True)

    def handle_request(self, write_file):
        try:
            # Drop first segment, as it's always empty
            segments = os.path.normpath(self.path).split("/")[1:]
            if not (len(segments) == 3 and segments[0:2] == ['.well-known', 'acme-challenge'] and self.is_base64url(segments[2])):
                raise IOError("Path invalid acme challenge: %s" % self.path)
            fetchpath = os.path.join(get_challengedir(), segments[2])
            with open(fetchpath, 'rb') as r:
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
            self.send_response(404, 'File not found')
            #self.log_error('Error: %s' % err)
            self.end_headers()
        except:
            self.send_response(500, 'Internal Server Error')
            #self.log_error('Error: %s' % err)
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


