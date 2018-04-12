#!/usr/bin/env python

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
typ,[data] = conn.search(None, "UNSEEN")
if typ != "OK":
    sys.exit("search failed")
for id in data.split():
    typ,data = conn.fetch(id, "(RFC822)")
    raw = data[0][1]
    msg = email.message_from_bytes(raw)
    print ("subject={}".format(get_header(msg, "Subject")))
    print ("from={}".format(get_header(msg, "From")))
    
# https://qiita.com/croquisdukke/items/2b7fabbe9df95e28f084
imap_idletag = conn._new_tag()
conn.send(b'%s IDLE\r\n'%(imap_idletag))
print('Waiting for a message...')
while True:
    imap_line = conn.readline().strip().decode('utf-8');
    print ("imap_list={}".format(imap_line))
    if imap_line.startswith('* BYE ') or (len(imap_line) == 0):
        print('Jumping out of a loop.')
        flag = False
        break
    if imap_line.endswith('EXISTS'):
        print('You got a message.')
        conn.send(b'DONE\r\n')
        imap_line = conn.readline().strip().decode('utf-8');
        print ("imap_list={}".format(imap_line))
        if imap_line.startswith('{} OK'.format(imap_idletag.decode('utf-8'))):
            print('Terminating IDLE mode')
            flag = True
        else :
            print('Failed to terminate')
            flag = False
        break
print ("flag={}".format(flag))

print ("done")
