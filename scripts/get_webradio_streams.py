#!/usr/bin/env python3
"""
Author : otszk (https://github.com/otszk)
Date   : 2024-04-17
Purpose: Scrape webradio streaming URLs
"""

import argparse
import csv
import datetime
import json
import os
import sys
from collections import namedtuple
from typing import NamedTuple, TextIO

import matrix_commander
import requests
from icecream import ic  # type: ignore
from lxml import html
from matrix_commander import main


class Args(NamedTuple):
    """Command-line arguments"""

    radio_file: TextIO
    dryrun: bool
    nomessage: bool
    debug: bool


# --------------------------------------------------------------------------------------
def get_args() -> Args:
    """Gets command-line arguments"""

    parser = argparse.ArgumentParser(
        description="Scrape webradio streaming URLs",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-r",
        "--radio_file",
        help="CSV containg webradio information",
        metavar="FILE",
        type=argparse.FileType("r", encoding="UTF-8"),
        default=os.path.expanduser("~") + "/.config/webradios/webradios.csv",
    )

    parser.add_argument("--dryrun", action="store_true", help="Skip JSON file update")

    parser.add_argument("--nomessage", action="store_true", help="Skip Matrix message")

    parser.add_argument(
        "-d", "--debug", action="store_true", help="Turn debug messages on"
    )

    args = parser.parse_args()

    return Args(args.radio_file, args.dryrun, args.nomessage, args.debug)


# --------------------------------------------------------------------------------------
def get_saved():
    """Opens a previously saved URLs JSON if it exists"""

    try:
        f = open(os.path.expanduser("~") + "/.local/share/webradio/urls.json", "r")
    except FileNotFoundError:
        ic("JSON file not found, a new one will be created")
        webradios = {}
    else:
        with f:
            try:
                webradios = json.load(f)
                f.close()
            except ValueError:
                exit("JSON decode error")

    webradios["last update"] = str(datetime.datetime.now())

    return webradios


# --------------------------------------------------------------------------------------
def get_stream(radio, webradios, log):
    """Extracts the radio stream URL from the provided website information"""

    try:
        page = requests.get(radio.url)
        if page.ok:
            tree = html.fromstring(page.content)
            xp = tree.xpath(radio.xpath)
            if len(xp) == 1:
                url = radio.prefix + xp[0]
                if radio.name not in webradios:
                    log.append(f"URL added: {radio.name}: {url}")
                elif webradios[radio.name] != url:
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

    return (webradios, log)


# --------------------------------------------------------------------------------------
def save_data(webradios):
    """Saves the updated stream URLs"""

    with open(
        os.path.expanduser("~") + "/.local/share/webradio/urls.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(webradios, f, ensure_ascii=False)
        f.close()


# --------------------------------------------------------------------------------------
def send_log(message):
    """Sends the log to a previously configured matrix chat room"""

    sys.argv[0] = "matrix-commander"
    sys.argv.extend(["-s", os.path.expanduser("~") + "/.config/matrix-commander/store"])
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


# --------------------------------------------------------------------------------------
def main() -> None:
    """Scrapes webradio stream URLs from sites and saves into a file"""

    args = get_args()

    if not args.debug:
        ic.disable()

    WebRadio = namedtuple("WebRadio", "name url xpath prefix")

    radio_infos = []
    for line in csv.reader(args.radio_file):
        radio_infos.append(WebRadio._make(line))
    ic(radio_infos)

    webradios = get_saved()

    log = []
    for radio in radio_infos:
        (webradios, log) = get_stream(radio, webradios, log)
    ic(webradios)

    if not args.dryrun:
        save_data(webradios)

    if not args.nomessage:
        if len(log) == 0:
            log.append("OK")
        send_log("\n".join(log))


# --------------------------------------------------------------------------------------
if __name__ == "__main__":
    main()


# vim: set colorcolumn=89:
