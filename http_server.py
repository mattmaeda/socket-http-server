import os
import re
import socket
import sys

MY_PATH = os.path.dirname(os.path.abspath(__file__))
WEBROOT = os.path.join(MY_PATH, "webroot")
BUFF_SIZE = 1024

def response(response_code, body, mimetype):
    return b"\r\n".join([
        b"HTTP/1.1 " + response_code,
        b"Content-Type: " + mimetype,
        b"",
        body
    ])

def response_ok(body=b"This is a minimal response", mimetype=b"text/html"):
    """
    returns a basic HTTP response
    Ex:
        response_ok(
            b"<html><h1>Welcome:</h1></html>",
            b"text/html"
        ) ->
        b'''
        HTTP/1.1 200 OK\r\n
        Content-Type: text/html\r\n
        \r\n
        <html><h1>Welcome:</h1></html>\r\n
        '''
    """
    return response(b"200 OK", body, mimetype)


def parse_request(request):
    (method, uri, version) =  request.split("\r\n")[0].split(" ")

    if method != "GET":
        return response_method_not_allowed()
    # Take care of trailing slash
    if len(uri) > 1 and uri.endswith("/"):
        uri = "".join(uri[0:-1])

    return uri


def response_method_not_allowed():
    """Returns a 405 Method Not Allowed response"""
    return response(b"405 Method Not Allowed",
                    b"<html><h1>Method Not Allowed</h1></html>",
                    b"text/html")


def response_not_found(message):
    """Returns a 404 Not Found response"""
    return response(b"404", b"<html><h1>" + message + b"</h1></html>",
                    b"text/html")


def resolve_uri(uri):
    """
    This method should return appropriate content and a mime type.

    If the requested URI is a directory, then the content should be a
    plain-text listing of the contents with mimetype `text/plain`.

    If the URI is a file, it should return the contents of that file
    and its correct mimetype.

    If the URI does not map to a real location, it should raise an
    exception that the server can catch to return a 404 response.

    Ex:
        resolve_uri('/a_web_page.html') -> (b"<html><h1>North Carolina...",
                                            b"text/html")

        resolve_uri('/images/sample_1.png')
                        -> (b"A12BCF...",  # contents of sample_1.png
                            b"image/png")

        resolve_uri('/') -> (b"images/, a_web_page.html, make_type.py,...",
                             b"text/plain")

        resolve_uri('/a_page_that_doesnt_exist.html') -> Raises a NameError

    """
    print("Processing uri '{}'".format(uri))
    content = b""
    mime_type = b"text/html"

    if uri == "/":
        content += b"<html><h1>" + WEBROOT.encode() + b"</h1><ul>"
        lineitem = "<li><a href=\"/{}\">{}</a></li>"

        for filename in os.listdir(WEBROOT):
            content += lineitem.format(filename, filename).encode()

        content += b"</html>"

    elif uri == "/images":
        content += (b"<html><h1>" + os.path.join(WEBROOT, "images").encode() +
                    b"</h1><ul>")
        lineitem = "<li><a href=\"/images/{}\">{}</a></li>"

        for filename in os.listdir(os.path.join(WEBROOT, "images")):
            content += lineitem.format(filename, filename).encode()

        content += b"</ul><a href=\"/\">Home</a></html>"

    elif os.path.exists(os.path.join(WEBROOT, "".join(uri[1:]))):
        if "images" in uri:
            mime_type = b"image/" + uri.split(".")[-1].encode()
        elif not uri.endswith("html"):
            mime_type = b"text/plain"

        with open(os.path.join(WEBROOT, "".join(uri[1:])), "rb") as webfile:
            content = bytearray(webfile.read())


    else:
        raise NameError("Path '{}' not found".format(uri))

    return content, mime_type


def server(log_buffer=sys.stderr):
    address = ('127.0.0.1', 10000)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    print("making a server on {0}:{1}".format(*address), file=log_buffer)
    sock.bind(address)
    sock.listen(1)

    try:
        while True:
            print('waiting for a connection', file=log_buffer)
            conn, addr = sock.accept()  # blocking
            request = ""
            try:
                print('connection - {0}:{1}'.format(*addr), file=log_buffer)
                while True:
                    data = conn.recv(BUFF_SIZE)
                    request += data.decode('utf8')

                    if len(data) < BUFF_SIZE:
                        break

                # Fulfill request
                uri = parse_request(request)

                if isinstance(uri, str):
                    (content, mimetype) = resolve_uri(uri)
                    response = response_ok(body=content, mimetype=mimetype)
                else:
                    # Kind of a hack.  This means method not allowed
                    response = uri

                conn.sendall(response)

            except NameError as ne:
                conn.sendall(response_not_found(str(ne).encode()))

            except ValueError as ne:
                conn.sendall(response_method_not_allowed())

            finally:
                conn.close()

    except KeyboardInterrupt:
        sock.close()
        return


if __name__ == '__main__':
    server()
    sys.exit(0)
