from flask import Flask, Response
from flask.json import jsonify

import threading

_REQUIRED_CONFIGS = ["enabled", "host", "port"]

app = Flask(__name__)

global_door_opener = None
global_config = None


def run(config, door_opener):
    global global_door_opener, global_config
    global_door_opener = door_opener
    global_config = config

    for c in _REQUIRED_CONFIGS:
        if c not in config.api_server:
            raise Exception("Missing required config '{}'".format(c))

    if config.api_server["enabled"]:
        app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

        threading.Thread(target=app.run, kwargs={
            "host": config.api_server["host"], "port": config.api_server["port"]}).start()


@app.route("/info")
def info():
    # Response.content_type = "application/json"
    return jsonify(
        {
            "door_opener": global_door_opener.serializable(),
            "config": global_config.serializable()
        }
    )


@app.route("/state", methods=["get"])
def state():
    return jsonify(global_door_opener.serializable())


@app.route("/open", methods=["put"])
def open():
    global_door_opener.open()
    return state()


@app.route("/close", methods=["put"])
def close():
    global_door_opener.close()
    return state()
