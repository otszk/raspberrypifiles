#!/usr/bin/python3 -u

from collections import namedtuple
from lxml import html
import datetime
import requests
import json
import getpass

# isort: skip_file
# isort: off
import sys
import os

import matrix_commander  # nopep8 # isort: skip
from matrix_commander import (
    main,
)  # nopep8 # isort: skip


def get_stream(radio):
    try:
        page = requests.get(radio.url)
        if page.ok:
            tree = html.fromstring(page.content)
            xp = tree.xpath(radio.xpath)
            if len(xp) == 1:
                url = radio.prefix + xp[0]
                if webradios[radio.name] != url:
                    log.append(
                        f"{radio.name}: URL update: {webradios[radio.name]} -> {url}"
                    )
                    webradios[radio.name] = url
            else:
                log.append(f"{radio.name}: XPath error")
        else:
            log.append(f"{radio.name}: HTTP status code: {page.status_code}")
    except requests.exceptions.RequestException as e:
        log.append(f"{radio.name}: {e}")


def send_log(message, user):
    sys.argv[0] = "matrix-commander"
    sys.argv.extend(["-s", "/home/" + user + "/.config/matrix-commander/store"])
    sys.argv.extend(["--log-level", "WARNING", "ERROR"])
    sys.argv.extend(["--message", message])

    try:
        ret = matrix_commander.main()
        if ret == 0:
            print("matrix_commander finished successfully.")
        else:
            print(f"matrix_commander failed with {ret} error{'' if ret == 1 else 's'}.")
    except Exception as e:
        print(f"Exception happened: {e}")
        ret = 99
    exit(ret)


user = getpass.getuser()

WebRadio = namedtuple("WebRadio", "name url xpath prefix")

log = []
radios = []
radios.append(
    WebRadio(
        "9 de Julho",
        "https://radio9dejulho.com.br/",
        "//audio/@src",
        "https:")
)
radios.append(
    WebRadio(
        "Cultura FM (Streema)",
        "http://streema.com/radios/play/Radio_Cultura_FM",
        "//@data-src",
        "",
    )
)
radios.append(
    WebRadio(
        "Cultura FM (UOL)",
        "https://cultura.uol.com.br/aovivo/4_ao-vivo-radio-cultura-fm.html",
        "//video/source/@src",
        "",
    )
)

with open("/home/" + user + "/.local/share/webradio/urls.json", "r") as f:
    webradios = json.load(f)
    f.close()

for radio in radios:
    get_stream(radio)

webradios["last update"] = str(datetime.datetime.now())

with open(
    "/home/" + user + "/.local/share/webradio/urls.json", "w", encoding="utf-8"
) as f:
    json.dump(webradios, f, ensure_ascii=False)

if len(log) == 0:
    log.append("OK")

send_log("\n".join(log), user)

# vim: set colorcolumn=89:
