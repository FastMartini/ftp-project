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
    command = "QUIT" + " " # build QUIT with CRLF terminator
    dataOut = command.encode("ascii") # encode ASCII bytes for control channel
    clientSocket.sendall(dataOut) # send QUIT over TCP
    dataIn = clientSocket.recv(1024) # read one reply chunk (e.g., 221 ...)
    data = dataIn.decode("ascii", "replace") # decode to text for display
    print(data) # show server's closing message
    clientSocket.close() # close control connection

def sendCommand(socket, command):
    """TODO: send CRLF-terminated command on control socket, return server reply."""
    dataOut = (command + "").encode("ascii") # append CRLF and encode
    socket.sendall(dataOut) # transmit on control socket
    dataIn = socket.recv(4096) # read server reply bytes
    data = dataIn.decode("ascii", "replace") # decode to text
    return data # return reply (e.g., '331 ...')

def receiveData(clientSocket):
    """TODO: recv from control socket and decode ASCII."""
    dataIn = clientSocket.recv(1024) # read greeting or reply
    data = dataIn.decode("ascii", "replace") # decode to printable string
    return data

# If you use passive mode you may want to use this method but you have to complete it
# You will not be penalized if you don't
def modePASV(clientSocket):
    """TODO: issue PASV, parse 227, open and return data socket."""
    data = sendCommand(clientSocket, "PASV") # ask server to enter PASV
    status = 0 # default (failure)
    dataSocket = None # placeholder


    if data.startswith("227"): # server accepted PASV
        status = 227 # mark success
        # Extract numbers inside parentheses: (h1,h2,h3,h4,p1,p2)
        start = data.find('(') # locate '('
        end = data.find(')', start) # locate matching ')'
        if start != -1 and end != -1: # ensure both exist
            nums = data[start+1:end].split(',') # split into list
            if len(nums) == 6: # must be 6 numbers
                h1,h2,h3,h4,p1,p2 = nums # unpack strings
                ip = f"{h1}.{h2}.{h3}.{h4}" # build dotted-quad IP
                port = (int(p1) << 8) + int(p2) # compute port = p1*256 + p2
                dataSocket = socket(AF_INET, SOCK_STREAM) # create TCP data socket
                dataSocket.connect((ip, port)) # connect to server's data endpoint
            else:
                status, dataSocket = 0, None # malformed tuple
        else:
            status, dataSocket = 0, None # missing parentheses
    return status, dataSocket # caller handles usage/close

def main():
    """Skeleton entry point; leaves all network logic TODO."""
    # Read target server from argv (per assignment usage)
    if len(sys.argv) != 2: # require exactly one arg
        print("Usage: python myftp.py <server-name-or-ip>")
        sys.exit(2) # exit with usage error
    HOST = sys.argv[1] # server name or IP


    # Prompt for credentials
    username = input("Enter the username: ") # e.g., demo
    password = input("Enter the password: ") # e.g., demopass


    # Create TCP control socket and connect to port 21
    clientSocket = socket(AF_INET, SOCK_STREAM) # TCP control socket
    clientSocket.connect((HOST, 21)) # connect to FTP control


    # Read server banner (expect 220)
    dataIn = receiveData(clientSocket) # get greeting text
    print(dataIn) # print greeting


    status = 0 # track login progress
    if dataIn.startswith("220"): # 220 Service ready
        status = 220 # update status


    # Send USER and print server reply
    print("Sending username") # log
    dataIn = sendCommand(clientSocket, f"USER {username}") # send USER
    print(dataIn) # show reply


    # Send PASS if required, then print server reply
    print("Sending password") # log
    if dataIn.startswith("331"): # 331 need password
        status = 331 # update status
        dataIn = sendCommand(clientSocket, f"PASS {password}") # send PASS
        print(dataIn) # show reply
    if dataIn.startswith("230"): # 230 logged in
        status = 230 # update status


    if status == 230: # proceed if logged in
        # Optional: probe PASV once (opens & closes data socket)
        pasvStatus, dataSocket = modePASV(clientSocket) # try PASV
        if pasvStatus == 227 and dataSocket is not None: # if success
            # Immediately close probe to keep skeleton light
            dataSocket.close() # close data channel


    # Disconnect cleanly
    print("Disconnecting...") # log
    clientSocket.close() # close control socket
    sys.exit() # Terminate the program after sending the corresponding data

main() # run entry point per skeleton
