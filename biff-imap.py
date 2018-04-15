#!/usr/local/bin/python3.6

import sys
import argparse
import getpass
import imaplib
import email

parser = argparse.ArgumentParser(description="Dumb Biff for IMAP")
parser.add_argument("--host", help="IMAP server", default="")
parser.add_argument("--port", help="IMAP port", default=None)
parser.add_argument("--ssl", help="use SSL", action="store_true")
parser.add_argument("--user", help="User", default=getpass.getuser())
parser.add_argument("--passwd", help="Password")
parser.add_argument("--inbox", help="inbox folder", default="inbox")
parser.add_argument("--full", help="full screen mode", action="store_true")
parser.add_argument("--noinit", help="show arrival messages only", action="store_true")
parser.add_argument("--debug", help="debug mode", action="store_true")
args = parser.parse_args()

if args.passwd is None:
    args.passwd = getpass.getpass()

if args.debug:
    print ("DEBUG: connect {!r} {!r}".format(args.host, args.port))
if args.ssl:
    imap_ctor = imaplib.IMAP4_SSL
else:
    imap_ctor = imaplib.IMAP4
if args.port:
    conn = imap_ctor(args.host, args.port)
else:
    conn = imap_ctor(args.host)

if args.debug:
    print ("DEBUG: LOGIN{!r}".format(args.user))
typ,[data] = conn.login(args.user, args.passwd)
del args.passwd	#give me consolation
if args.debug:
    print ("DEBUG: {!r} {!r}".format(typ, data))
if typ != "OK":
    sys.exit("login {!r} failure".format(args.user))

if args.debug:
    print ("DEBUG: SELECT {!r}".format(args.inbox))
typ,[data] = conn.select(args.inbox, readonly=True)
if args.debug:
    print ("DEBUG: {!r} {!r}".format(typ, data))
if typ != "OK":
    sys.exit("select {!r} failure".format(args.inbox))

def cls():
    if args.debug:
        print ("----")
        return
    #print ("\033[2J", end="")	#CSI n J -- Erase in Display
    #print ("\033[1;1H", end="")	#CSI n ; m H -- Cursor Position
    sys.stdout.write("\033[2J")		#CSI n J -- Erase in Display
    sys.stdout.write("\033[1;1H")	#CSI n ; m H -- Cursor Position
    sys.stdout.flush()

def bell():
    if args.debug:
        print ("bowwow")
        return
    print ("\a", end="")

def get_header(msg,key):
    v = msg[key]
    if v is None:
        return ""
    try:
        hdr = email.header.make_header(email.header.decode_header(v))
    except:
        return str(v)
    else:
        return str(hdr)

last_unseen = set()
def show_recent(nodisplay=False):
    global last_unseen
    if args.debug:
        print ("DEBUG: SEARCH UNSEEN")
    #typ,[data] = conn.search(None, "UNSEEN")
    typ,[data] = conn.uid("SEARCH", "UNSEEN")
    if args.debug:
        print ("DEBUG: {!r} {!r}".format(typ, data))
    if typ != "OK":
        sys.exit("search failed")
    unseen = data.split()
    if args.full:
        cls()
    n = 0
    for id in unseen:
        if nodisplay:
            continue
        if not args.full and id in last_unseen:
            continue
        if args.debug:
            print ("DEBUG: FETCH {!r}".format(id))
        #typ,data = conn.fetch(id, "(RFC822)")
        typ,data = conn.uid("FETCH", id, "(RFC822)")
        if args.debug:
            print ("DEBUG: {!r} {!r}".format(typ, data))
        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        print ("From: {}".format(get_header(msg, "From")))
        print ("To: {}".format(get_header(msg, "To")))
        print ("Subject: {}".format(get_header(msg, "Subject")))
        print ()
        n += 1
    last_unseen = set(unseen)
    return n

show_recent(nodisplay=args.noinit)

while True:
    tag = conn._new_tag()
    if args.debug:
        print ("DEBUG: IDLE")
    conn.send(b'%s IDLE\r\n'%(tag))
    done = False
    arrival = False
    done_sent = False
    while True:
        resp = conn.readline().strip().decode('utf-8');
        if args.debug:
            print ("DEBUG: {!r}".format(resp))
        if resp.startswith('* BYE ') or (len(resp) == 0):
            break
        if resp.startswith("* "):
            if resp.split()[2] == "EXISTS":
                done = True
                arrival = True
            if args.full:
                if resp.split()[2] == "EXPUNGE":
                    done = True
                if resp.split()[2] == "FETCH":
                    done = True
        if done and not done_sent:
            if args.debug:
                print ("DEBUG: DONE")
            conn.send(b'DONE\r\n')
            done_sent = True
            
        if resp.startswith('{} OK'.format(tag.decode('utf-8'))):
            break
    n = show_recent()
    if n > 0 and arrival:
        bell()

