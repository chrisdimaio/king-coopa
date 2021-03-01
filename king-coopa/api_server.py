from flask import Flask, Response, request
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
        app.config["UPLOAD_FOLDER"] = ""
        app.config["MAX_CONTENT_PATH"] = 4096

        threading.Thread(target=app.run, kwargs={
            "host": config.api_server["host"], "port": config.api_server["port"]}).start()


@app.route("/info")
def info():
    from subprocess import check_output

    return jsonify(
        {
            "door_opener": global_door_opener.serializable(),
            "config": global_config.serializable(),
            "system": {
                "cpu_temp": int(
                    check_output(
                        ["cat", "/sys/class/thermal/thermal_zone0/temp"]).decode("utf-8").rstrip()
                ) / 1000
            }
        }
    )


@app.route("/state", methods=["get"])
def state():
    return jsonify(global_door_opener.serializable())


@app.route("/close", methods=["put"])
def close():
    global_door_opener.close()
    return state()


@app.route("/open", methods=["put"])
def open():
    global_door_opener.open()
    return state()


@app.route("/restart", methods=["put"])
def restart():
    import subprocess
    subprocess.Popen(["sudo", "systemctl", "restart", "king-coopa"])
    return jsonify({"Success": True})


@app.route('/reconfigure', methods=["post"])
def reconfigure():
    import builtins
    import subprocess
    import yaml
    from yaml.loader import FullLoader
    try:
        # Backup the current config
        subprocess.Popen(["mv", "config.yaml", "config.yaml.previous"])
        with builtins.open("config.yaml", "w") as f:
            yaml.dump(yaml.load(request.data, Loader=FullLoader), f)
        restart()
    except yaml.YAMLError as exc:
        print(exc)
    return jsonify({"Success": True})
