#!/usr/bin/env python3
# vi:shiftwidth=4:expandtab:

import argparse
import email
import getpass
import imaplib
import sys

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
    print("DEBUG: connect {!r} {!r}".format(args.host, args.port))
if args.ssl:
    imap_ctor = imaplib.IMAP4_SSL
else:
    imap_ctor = imaplib.IMAP4
if args.port:
    conn = imap_ctor(args.host, args.port)
else:
    conn = imap_ctor(args.host)

if args.debug:
    print("DEBUG: LOGIN{!r}".format(args.user))
typ, [data] = conn.login(args.user, args.passwd)
del args.passwd  # give me consolation
if args.debug:
    print("DEBUG: {!r} {!r}".format(typ, data))
if typ != "OK":
    sys.exit("login {!r} failure".format(args.user))

if args.debug:
    print("DEBUG: SELECT {!r}".format(args.inbox))
typ, [data] = conn.select(args.inbox, readonly=True)
if args.debug:
    print("DEBUG: {!r} {!r}".format(typ, data))
if typ != "OK":
    sys.exit("select {!r} failure".format(args.inbox))


def cls():
    if args.debug:
        print("---cls---")
        return
    sys.stdout.write("\033[2J")    # ED: CSI n J -- Erase in Display
    sys.stdout.write("\033[1;1H")  # CUP: CSI n ; m H -- Cursor Position
    sys.stdout.flush()


def alt_screen():
    sys.stdout.write("\033[?1049h")  # DECSET XT_EXTSCRN
    sys.stdout.flush()


def normal_screen():
    sys.stdout.write("\033[?1049l")  # DECRST XT_EXTSCRN
    sys.stdout.flush()


def bell():
    if args.debug:
        print("---bowwow---")
        return
    sys.stdout.write("\007")
    sys.stdout.flush()


def get_header(msg, key):
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
        print("DEBUG: SEARCH UNSEEN")
    typ, [data] = conn.uid("SEARCH", "UNSEEN")
    if args.debug:
        print("DEBUG: {!r} {!r}".format(typ, data))
    if typ != "OK":
        sys.exit("search failed")
    unseen = data.split()
    if args.full:
        cls()
    n_new = 0
    n_show = 0
    for id in unseen:
        if nodisplay:
            continue
        if id not in last_unseen:
            n_new += 1
            if not args.full:
                continue
        if args.debug:
            print("DEBUG: FETCH {!r}".format(id))
        typ, data = conn.uid("FETCH", id, "(RFC822.HEADER)")
        if args.debug:
            print("DEBUG: {!r} {!r}".format(typ, data))
        n_show += 1
        raw = data[0][1]
        msg = email.message_from_bytes(raw)
        print("[{}]".format(n_show))
        print("From: {}".format(get_header(msg, "From")))
        print("To: {}".format(get_header(msg, "To")))
        print("Subject: {}".format(get_header(msg, "Subject")))
        print()
    last_unseen = set(unseen)
    if args.debug:
        print("DEBUG: n_new={!r}".format(n_new))
    return n_new


def loop():
    while True:
        tag = conn._new_tag()
        if args.debug:
            print("DEBUG: IDLE")
        conn.send(b'%s IDLE\r\n' % (tag))
        done = False
        arrival = False
        done_sent = False
        while True:
            resp = conn.readline().strip().decode('utf-8')
            if args.debug:
                print("DEBUG: {!r}".format(resp))
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
                    print("DEBUG: DONE")
                conn.send(b'DONE\r\n')
                done_sent = True

            if resp.startswith('{} OK'.format(tag.decode('utf-8'))):
                break
        n_new = show_recent()
        if n_new > 0 and arrival:
            bell()


def main():
    try:
        if args.full:
            alt_screen()
        show_recent(nodisplay=args.noinit)
        loop()
    except:
        if args.full:
            normal_screen()
        raise


try:
    main()
except KeyboardInterrupt:
    pass
