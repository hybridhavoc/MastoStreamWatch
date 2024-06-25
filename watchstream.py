from datetime import datetime, timedelta
from collections import Counter
import websockets
import itertools
import re
import json
import os
import re
import sys
import requests
import argparse
import logging
import asyncio

async def listen(arguments):
    wss_url = f"wss://{arguments.server}/api/v1/streaming?access_token={arguments.access_token}&stream=public"
    pl("info", "  Connecting...")

    async for websocket in websockets.connect(wss_url):
        try:
            while True:
                result = await websocket.recv()
                resultJson = json.loads(result)
                if resultJson["event"] == "update":
                    payload = json.loads(resultJson["payload"])
                    regex_check(arguments, payload)
        except websockets.ConnectionClosed:
            continue

def regex_check(arguments, payload):
    regexes = []
    content = payload["content"]
    contentId = payload["id"]
    account = payload["account"]

    # Pull regexes from the regex file
    if os.path.exists(arguments.regex_file):
        with open(arguments.regex_file, "r", encoding="utf-8") as f:
            regexes = f.read().splitlines()
    else:
        pl("error",f"Regexes file could not be found")

    # Perform check
    for r in regexes:
        if re.search(f"({r})", content):
            # Regex match found, submitting report
            pl("info", f"{account["id"]} : {contentId} : Regex check found: {r}")
            submit_report(arguments.server, arguments.access_token, payload)

def submit_report(server,access_token,payload):
    contentIds = []
    contentIds.append(payload["id"])
    account = payload["account"]
    #Submitting report
    report_json = {
        "account_id": account["id"],
        "comment": f"Potential spam account, automatically determined via script. Please contact @hybridhavoc@darkfriend.social if invalid.",
        "forward": "false",
        "category": "spam",
        "status_ids": contentIds,
        "forward": "false"
    }
    report_url = f"https://{server}/api/v1/reports"
    report_resp = requests.post(report_url, headers={"User-Agent":user_agent(),"Authorization": f"Bearer {access_token}"}, json=report_json, timeout=30)
    if report_resp.status_code == 200:
        pl("info",f"{account['id']} : Report filed")
    else:
        pl("error",f"{account['id']} : Problem submitting report. Status code: {report_resp.status_code}")

def user_agent():
    return f"MastoStreamWatch; +{arguments.server}"

def pl(level,message):
    match level:
        case "debug":
            logging.debug(message)
        case "info":
            logging.info(message)
        case "error":
            logging.error(message)
        case _:
            logging.info(message)
    print(message)

if __name__ == "__main__":
    # Getting arguments
    argparser=argparse.ArgumentParser()
    argparser.add_argument('-c','--config', required=False, type=str, help='Optionally provide a path to a JSON file containing configuration options. If not provided, options must be supplied using command line flags.')
    argparser.add_argument('--server', required=False, help="Required: The name of your server (e.g. `darkfriend.social`)")
    argparser.add_argument('--access-token', action="append", required=False, help="Required: The access token can be generated at https://<server>/settings/applications")
    argparser.add_argument('--regex-file', action="append", required=False, default="regex", help="A file that contains the regex strings to check against. Default: regex")
    argparser.add_argument('--log-directory', required=False, default="logs", help="Directory to store logs")
    argparser.add_argument('--logging-level', required=False, default="info", choices=['info','debug','error'], help="Loggin level.")
    arguments = argparser.parse_args()

    # Pulling from config file
    if(arguments.config != None):
        if os.path.exists(arguments.config):
            with open(arguments.config, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            for key in config:
                setattr(arguments, key.lower().replace('-','_'), config[key])

        else:
            print(f"Config file {arguments.config} doesn't exist")
            sys.exit(1)
    
    # If no server or access token are specified, quit
    if(arguments.server == None or arguments.access_token == None):
        print("You must supply at least a server name and access token")
        sys.exit(1)

    # in case someone provided the server name as url instead, 
    setattr(arguments, 'server', re.sub(r"^(https://)?([^/]*)/?$", "\\2", arguments.server))

    # check if the provided regex file exists
    if(arguments.regex_file != None):
        if not os.path.exists(arguments.regex_file):
            print("The regex file cannot be found.")
    else:
        print("Somehow no regex file was specified")

    # logging
    LOG_FILE_DATETIME = datetime.now().strftime("%Y-%m-%d")
    LOG_FILE = arguments.log_directory + "\\log_" + LOG_FILE_DATETIME + ".txt"
    def switch(loglevel):
        if loglevel == "info":
            return logging.INFO
        elif loglevel == "debug":
            return logging.DEBUG
        elif loglevel == "error":
            return logging.ERROR
        else:
            raise Exception(f"{arguments.loglevel} is not a valid logging level. Log level should be debug, info, or error")
    logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',filename=LOG_FILE, level=switch(arguments.logging_level), datefmt='%Y-%m-%d %H:%M:%S')

    # really starting
    pl("info", "  Script starting")

    # websocket connection
    asyncio.run(listen(arguments))