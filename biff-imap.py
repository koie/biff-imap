#!/usr/local/bin/python3.6

import sys
import getpass
import imaplib
import email

host = "mail2.suri.co.jp"
port = 143
user = getpass.getuser()
pswd = getpass.getpass()
inbox = "inbox"

def get_header(msg,key):
    v = msg[key]
    if v is None:
        return ""
    hdr = email.header.make_header(email.header.decode_header(v))
    return str(hdr)

conn = imaplib.IMAP4(host, port)
typ,[data] = conn.login(user, pswd)
if typ != "OK":
    sys.exit("login filed")
typ,[data] = conn.select(inbox, readonly=True)
if typ != "OK":
    sys.exit("select failed")
#typ,[data] = conn.search(None, "ALL")

last_unseen = set()
def show_recent():
    global last_unseen
    typ,[data] = conn.search(None, "UNSEEN")
    if typ != "OK":
        sys.exit("search failed")
    unseen = data.split()
    for id in unseen:
        if id in last_unseen:
            continue
        typ,data = conn.fetch(id, "(RFC822)")
        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        print ("{} {}".format(get_header(msg, "From"), get_header(msg, "Subject")))
    last_unseen = set(unseen)

def bell():
        print("\a", end="")
        
show_recent()
print ("---")

while True:
    imap_idletag = conn._new_tag()
    conn.send(b'%s IDLE\r\n'%(imap_idletag))
    while True:
        resp = conn.readline().strip().decode('utf-8');
        #print ("resp={}".format(resp))
        if resp.startswith('* BYE ') or (len(resp) == 0):
            break
        if resp.startswith("* "):
            if resp.endswith('EXISTS'):
                conn.send(b'DONE\r\n')
        if resp.startswith('{} OK'.format(imap_idletag.decode('utf-8'))):
            break
    show_recent()
    bell()
