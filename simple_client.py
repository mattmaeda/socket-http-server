import socket

BUFF_SIZE = 1024

def client(message):
    server_address = ("localhost", 10000)
    sock = socket.socket()
    sock.connect(server_address)

    received_message = ""

    try:
        print("sending '{}'".format(message))
        sock.send(message.encode("utf8"))

        while True:
            chunk = sock.recv(BUFF_SIZE)
            received_message += chunk.decode("utf8")

            if len(chunk) < BUFF_SIZE:
                break
    finally:
        sock.close()
        print("received '{}'".format(received_message))
        return received_message
