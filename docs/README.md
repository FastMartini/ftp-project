## Implementation Notes

- We implemented `myftp.py` **using the provided skeleton code as-is**, filling in only the required logic with raw sockets (no FTP libraries), per the assignment.

## Testing Summary (macOS) — inet.cs.fiu.edu

We tested `myftp.py` against `inet.cs.fiu.edu` (`demo/demopass`) instead of running a local Docker server to avoid extra setup.

### What works / what to expect as non-owners

- `ls` ✅  
  Works as expected. Shows directory permissions (e.g., `drwx------`) that explain why other commands fail.

- `cd <dir>` ❌ → **550**  
  We’re not the owner; directories are not world-executable/readable, so `cd` returns 550.

- `get <file>` ❌ → **550**  
  We don’t have read permission on files in the tested location, so downloads are denied.

- `put <local-file>` ⚠️  
  The server **does create** an entry in the remote (ftp-project) root, but it **cannot be opened/read afterward** (permissions). Follow-up access attempts yield 550.

- `delete <remote-file>` ❌ → **550**  
  As non-owners, we do not have permission to remove files; delete operations return 550.

- `quit` ✅  
  Cleanly closes the session (221).

### Reproduce (example)

```bash
python3 myftp.py inet.cs.fiu.edu
# Username: demo
# Password: demopass

myftp> ls          # 150 ... ; 226 Directory send OK
myftp> cd folder   # 550 (not owner)
myftp> get file    # 550 (not owner / no read)
myftp> put test.txt  # creates entry but cannot open afterward (permissions)
myftp> quit        # 221 Goodbye
