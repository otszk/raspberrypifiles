#!/usr/bin/python3 -u

import subprocess
import signal
import json
import getpass

user = getpass.getuser()

with open("/home/" + user + "/.local/share/webradio/urls.json") as json_file:
    webradios = json.load(json_file)

run = True


def handler_stop_signals(signum, frame):
    global run
    run = False


signal.signal(signal.SIGINT, handler_stop_signals)
signal.signal(signal.SIGTERM, handler_stop_signals)

while run:
    player = subprocess.run(
        ["mpv", "--no-video", webradios["9 de Julho"], "--volume=40"],
        #["mpv", "--no-video", webradios["Cultura FM (Streema)"], "--volume=50"],
        env={"XDG_RUNTIME_DIR": "/run/user/1000"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

# vim: set colorcolumn=89:
