## Dehydrated ACME Responder

ACME Responder is a systemd socket-activated web server, currently focussed to
run with the dehyrated ACME client. It will expose the response to the ACME
challenges at .well-known/acme-challenges directory. It will return 404 for any
other requested path.

For testing purposes, the responder can be executed stand-alone, in which case
it will bind to port 8080. Use the -p argument to bind to a custom port.
