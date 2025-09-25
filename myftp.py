# Help: https://www.eventhelix.com/networking/ftp/
# Help: https://www.eventhelix.com/networking/ftp/FTP_Port_21.pdf
# Help: https://realpython.com/python-sockets/
# Help: PASV mode may be easier in the long run. Active mode works
# Reading: https://unix.stackexchange.com/questions/93566/ls-command-in-ftp-not-working
# Reading: https://stackoverflow.com/questions/14498331/what-should-be-the-ftp-response-to-pasv-command

from socket import *                 # socket API (as required by skeleton)
import sys                           # for sys.exit

def quitFTP(clientSocket):
    """TODO: send QUIT and print reply, then close control socket."""
    pass  # placeholder

def sendCommand(socket, command):
    """TODO: send CRLF-terminated command on control socket, return server reply."""
    return ""  # placeholder so callers have a string

def receiveData(clientSocket):
    """TODO: recv from control socket and decode ASCII."""
    return ""  # placeholder

# If you use passive mode you may want to use this method but you have to complete it
# You will not be penalized if you don't
def modePASV(clientSocket):
    """TODO: issue PASV, parse 227, open and return data socket."""
    # command = "PASV" + "\r\n"   # keep commented until implemented
    status = 0
    return status, None  # placeholder

def main():
    """Skeleton entry point; leaves all network logic TODO."""
    username = input("Enter the username: ")
    password = input("Enter the password: ")

    clientSocket = socket(AF_INET, SOCK_STREAM)   # control socket placeholder
    # HOST = ""                   # TODO: set server name/IP
    # clientSocket.connect((HOST, 21))  # TODO
    # dataIn = receiveData(clientSocket); print(dataIn)

    status = 0
    if "" .startswith(""):        # placeholder branch kept to match skeleton
        pass                      # indent with a body (do nothing)

    print("Skeleton loaded. Implement connect/login/commands next.")

    try:
        clientSocket.close()
    except Exception:
        pass
    sys.exit()  # Terminate program (skeleton only)

if __name__ == "__main__":
    main()
