import Dashboard.service
from Dashboard import socket, time

# remote_ip = Dashboard.service.SiglentIP  # should match the instrument’s IP address
port = 5024  # the port number of the instrument service


def SocketConnect():
    try:
        # create an AF_INET, STREAM socket (TCP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('Failed to create socket.')
        Dashboard.service.SiglentIP = None
    try:
        # Connect to remote server
        s.connect((Dashboard.service.SiglentIP, port))
    except socket.error:
        print('failed to connect to ip ' + Dashboard.service.SiglentIP)
        Dashboard.service.SiglentIP = None
    return s


def SocketSend(Sock, cmd):
    try:
        # Send cmd string
        Sock.sendall(cmd)
        Sock.sendall(b'\n')
        time.sleep(0.4)
    except socket.error:
        # Send failed
        print('Send failed')
        Dashboard.service.SiglentIP = None
    # reply = Sock.recv(4096)
    # return reply


def SocketClose(Sock):
    Sock.close()
    time.sleep(0.4)


#################################
# The idea might be to user input
# ch1/ch2 and to turn on/off
#################################


def ON():
    s = SocketConnect()
    SocketSend(s, b'C1:OUTP ON')  # Set CH1 ON
    SocketSend(s, b'C2:OUTP ON')  # test
    SocketClose(s)  # Close socket
    print('Query complete.')


def OFF():
    s = SocketConnect()
    SocketSend(s, b'C1:OUTP OFF')
    SocketClose(s)  # Close socket
    print('Query complete.')
