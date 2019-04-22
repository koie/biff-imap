IMAP_SERVER = YOUR.MAIL.SERVER.COM
run::
	env LANG=ja_JP.UTF-8 ./biff-imap.py --host $(IMAP_SERVER) --full #--debug
