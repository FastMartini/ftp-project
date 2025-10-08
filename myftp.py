# Help: https://www.eventhelix.com/networking/ftp/
# Help: https://www.eventhelix.com/networking/ftp/FTP_Port_21.pdf
# Help: https://realpython.com/python-sockets/
# Help: PASV mode may be easier in the long run. Active mode works
# Reading: https://unix.stackexchange.com/questions/93566/ls-command-in-ftp-not-working
# Reading: https://stackoverflow.com/questions/14498331/what-should-be-the-ftp-response-to-pasv-command

from socket import *                  # import raw TCP socket APIs (no FTP libs)               
import sys                            # for command-line args and exit    
                     
CRLF = "\r\n"

def q(s): 
    return f'"{s}"' if ' ' in s else s

def quitFTP(clientSocket):
    """Send QUIT and print the server reply, then close the control socket."""
    command = "QUIT" + "\r\n"                 # build QUIT with CRLF terminator               
    dataOut = command.encode("ascii")         # encode ASCII bytes for control channel          
    clientSocket.sendall(dataOut)             # send QUIT over TCP                               
    dataIn = clientSocket.recv(4096)          # read one reply chunk (e.g., 221 ...)             
    data = dataIn.decode("ascii", "replace")  # decode to text for display                      
    print(data)                               # show server's closing message                    
    clientSocket.close()                      # close control connection                          


def sendCommand(socket, command):
    """Send one FTP command line and return the immediate server reply as text."""
    dataOut = (command + "\r\n").encode("ascii")  # append CRLF and encode                      
    socket.sendall(dataOut)                           # transmit on control socket                  
    dataIn = socket.recv(4096)                        # read server reply bytes                     
    data = dataIn.decode("ascii", "replace")        # decode to text                               
    return data                                       # return reply (e.g., '331 ...')              


def receiveData(clientSocket):
    """Receive a chunk from the control socket and return decoded text (banner)."""
    dataIn = clientSocket.recv(4096)                  # read greeting or reply                       
    data = dataIn.decode("ascii", "replace")         # decode to printable string                   
    return data                                       # give back to caller                          


# If you use passive mode you may want to use this method but you have to complete it
# You will not be penalized if you don't

def modePASV(clientSocket):
    data = sendCommand(clientSocket, "PASV")
    if data.startswith("227"):
        a, b = data.find('('), data.find(')')
        if a != -1 and b != -1:
            nums = data[a+1:b].split(',')
            if len(nums) == 6:
                p1, p2 = int(nums[4]), int(nums[5])
                port = (p1 << 8) + p2
                ip = clientSocket.getpeername()[0]  # use control peer IP (fixes Docker/NAT)
                s = socket(AF_INET, SOCK_STREAM); s.settimeout(10); s.connect((ip, port))
                return 227, s
    # Fallback: EPSV (better behind NAT)
    data = sendCommand(clientSocket, "EPSV")
    if data.startswith("229"):
        inside = data[data.find('(')+1:data.find(')')]
        parts = inside.split('|')  # format: (|||port|)
        port = int(parts[-2])
        ip = clientSocket.getpeername()[0]
        s = socket(AF_INET, SOCK_STREAM); s.settimeout(10); s.connect((ip, port))
        return 229, s
    print("PASV/EPSV failed:", data.strip())
    return 0, None# caller handles usage/close                    


def main():
    """Connect/login, switch TYPE I, and implement ls/cd/get/put/delete/quit REPL."""
    # --- parse target server from argv ---
    if len(sys.argv) != 2:                            # require exactly one arg                        
        print("Usage: python myftp.py <server-name-or-ip>")  # usage text                            
        sys.exit(2)                                   # exit with usage error                          
    HOST = sys.argv[1]                                # server name or IP                              

    # --- prompt for credentials ---
    username = input("Enter the username: ")          # e.g., demo                                     
    password = input("Enter the password: ")          # e.g., demopass                                 

    # --- open control connection ---
    clientSocket = socket(AF_INET, SOCK_STREAM)       # create TCP control socket 
    clientSocket.settimeout(10) # adds timeout                   
    clientSocket.connect((HOST, 21))                  # connect to FTP control port                    

    # --- read banner and validate 220 ---
    dataIn = receiveData(clientSocket)                # get greeting                                    
    print(dataIn)                                     # print greeting                                  
    if not dataIn.startswith("220"):                  # ensure service ready                           
        print("Failure: unexpected greeting; closing.")  # error message                                
        quitFTP(clientSocket)                         # attempt graceful quit                          
        sys.exit(1)                                   # stop program                                    

    # --- USER/PASS login ---
    print("Sending username")                         # log action                                     
    dataIn = sendCommand(clientSocket, f"USER {username}")  # send USER                                   
    print(dataIn)                                     # print reply                                     

    print("Sending password")                         # log action                                     
    if dataIn.startswith("331"):                      # 331 need password                              
        dataIn = sendCommand(clientSocket, f"PASS {password}")  # send PASS                               
        print(dataIn)                                 # print reply                                     
    elif not dataIn.startswith("230"):               # not 331 or 230 → fail                          
        print("Failure: USER rejected; closing.")     # error                                          
        quitFTP(clientSocket)                         # quit                                            
        sys.exit(1)                                   # stop                                            

    if not dataIn.startswith("230"):                  # must be logged in                              
        print("Failure: login failed; closing.")      # error                                          
        quitFTP(clientSocket)                         # quit                                            
        sys.exit(1)                                   # stop                                            

    # --- set binary mode (TYPE I) ---
    t = sendCommand(clientSocket, "TYPE I")           # request image (binary) mode                    
    print(t.strip())                                  # print mode switch reply                         

    # --- interactive command loop ---
    while True:                                       # REPL until 'quit'                               
        try:
            line = input("myftp> ").strip()           # read a command line                            
        except (EOFError, KeyboardInterrupt):         # Ctrl-D/Ctrl-C                                  
            print()                                   # newline for cleanliness                         
            quitFTP(clientSocket)                     # graceful quit                                   
            sys.exit(0)                               # exit success                                    

        if not line:                                  # ignore empty input                              
            continue                                  # prompt again                                    

        tokens = line.split()                         # split into tokens                               
        cmd = tokens[0].lower()                       # first token is command                          

        # ---------------- ls ----------------
        if cmd == 'ls':                               # list remote directory                           
            pasvStatus, dataSocket = modePASV(clientSocket)  # enter passive mode                       
            if pasvStatus in (227, 229) and dataSocket is not None: # proceed if data socket ready             
                pre = sendCommand(clientSocket, "LIST")       # ask server to list                       
                print(pre.strip())                              # print pre-transfer reply (150/125)  
                if not (pre.startswith("150") or pre.startswith("125")):
                    print("Failure:", pre.strip()); dataSocket.close(); continue     
                listing = b""                                   # buffer for directory bytes               
                while True:                                     # read until server closes data socket     
                    chunk = dataSocket.recv(4096)               # read a chunk from data channel          
                    if not chunk:                               # EOF on data channel                      
                        break                                   # stop loop                                
                    listing += chunk                            # append chunk                              
                dataSocket.close()                              # close data socket                         
                try:
                    print(listing.decode('utf-8'))              # try UTF-8 for directory text              
                except UnicodeDecodeError:
                    print(listing.decode('latin-1', 'replace')) # fallback for non-UTF8 servers            
                post = receiveData(clientSocket)                # read completion reply (expect 226)        
                print(post.strip())                             # print completion                          
            else:
                print("Failure: PASV setup failed for ls")     # report error                              

        # ---------------- cd <remote-dir> ----------------
        elif cmd == 'cd':                           # change working directory on server               
            if len(tokens) != 2:                    # ensure exactly one argument                      
                print("Failure: Usage: cd <remote-dir>")       # usage hint                                 
            else:
                arg = tokens[1]
                resp = sendCommand(clientSocket, f'CWD {q(arg)}')  # issue CWD                          
                print(resp.strip())                   # print server reply (250 on success)             

        # ---------------- get <remote-file> ----------------
        elif cmd == 'get':                           # download a file from server                      
            if len(tokens) != 2:                     # ensure one filename                              
                print("Failure: Usage: get <remote-file>")    # usage hint                                 
                continue                              # back to prompt                                   
            remote = tokens[1]                        # remote file path/name                            
            local = remote.split('/')[-1]             # save as basename locally                         
            pasvStatus, dataSocket = modePASV(clientSocket)   # prepare data channel                       
            if pasvStatus in (227, 229) and dataSocket is not None:  # proceed if OK                              
                pre = sendCommand(clientSocket, f'RETR "{remote}"')  # request file                         
                print(pre.strip())                    # print pre-transfer reply (150/125)   
                if not (pre.startswith("150") or pre.startswith("125")):
                    print("Failure:", pre.strip())
                    dataSocket.close()
                    continue            
                bytes_recv = 0                        # counter for bytes received                       
                with open(local, 'wb') as f:          # open local file for binary write                 
                    while True:                       # read until EOF on data socket                    
                        chunk = dataSocket.recv(4096) # read a data chunk                               
                        if not chunk:                 # connection closed by server                      
                            break                     # stop reading                                     
                        f.write(chunk)                # write chunk to file                              
                        bytes_recv += len(chunk)      # update counter                                   
                dataSocket.close()                    # close data socket                                
                post = receiveData(clientSocket)      # read completion reply (expect 226)               
                print(post.strip())                   # print completion                                 
                print(f"Success: Downloaded {bytes_recv} bytes to '{local}'")  # report bytes            
            else:
                print("Failure: PASV setup failed for get")  # error path                                

        # ---------------- put <local-file> ----------------
        elif cmd == 'put':                           # upload a local file to server                     
            if len(tokens) != 2:                     # ensure one argument                               
                print("Failure: Usage: put <local-file>")     # usage hint                                  
                continue                              # back to prompt                                    
            local = tokens[1]                         # path to local file                                
            try:
                f = open(local, 'rb')                 # try to open local file for reading               
            except FileNotFoundError:
                print(f"Failure: Local file not found: {local}")  # report missing file                  
                continue                              # skip                                             
            pasvStatus, dataSocket = modePASV(clientSocket)   # open data channel                          
            if pasvStatus in (227, 229) and dataSocket is not None:  # proceed if OK 
                remote_name = local.split('/')[-1]                             
                pre = sendCommand(clientSocket, f'STOR "{remote_name}"') # announce upload       
                print(pre.strip())                    # print pre-transfer reply (150/125)
                
                if not (pre.startswith("150") or pre.startswith("125")):
                    print("Failure:", pre.strip())   # likely 550 Permission denied
                    dataSocket.close()
                    continue               
                
                bytes_sent = 0                        # counter for bytes sent                           
                with f:                               # ensure file closed after sending                 
                    while True:                       # loop until EOF                                   
                        chunk = f.read(4096)          # read next block                                  
                        if not chunk:                 # EOF reached                                      
                            break                     # stop loop                                        
                        dataSocket.sendall(chunk)     # transmit chunk on data channel                   
                        bytes_sent += len(chunk)      # update counter                                   
                try:
                    dataSocket.shutdown(SHUT_WR)      # signal EOF to server (best effort)               
                except Exception:
                    pass                              # ignore if not supported                           
                dataSocket.close()                    # close the data socket                             
                post = receiveData(clientSocket)      # read completion (expect 226)                      
                print(post.strip())                   # print completion                                  
                print(f"Success: Uploaded {bytes_sent} bytes from '{local}'")  # report bytes            
            else:
                print("Failure: PASV setup failed for put")  # error path                                

        # ---------------- delete <remote-file> ----------------
        elif cmd == 'delete':                        # delete file on server                             
            if len(tokens) != 2:                     # ensure one argument                               
                print("Failure: Usage: delete <remote-file>")  # usage hint                               
            else:
                resp = sendCommand(clientSocket, f'DELE "{tokens[1]}"')  # issue delete                    
                print(resp.strip())                   # print server reply (250 on success)              

        # ---------------- quit ----------------
        elif cmd == 'quit':                          # end session politely                              
            quitFTP(clientSocket)                    # send QUIT and close control                       
            sys.exit(0)                              # terminate program                                 

        # ---------------- unknown ----------------
        else:                                        # any other verb                                     
            print(f"Failure: Unknown command '{cmd}'")  # helpful error message                         


# Run the entry point (per skeleton)
main()                                             # start program execution                           
