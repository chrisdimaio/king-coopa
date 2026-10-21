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
    from datetime import datetime
    from subprocess import check_output

    return jsonify(
        {
            "door_opener": global_door_opener.serializable(),
            "config": global_config.serializable(),
            "system": {
                "time": datetime.now().strftime("%A %B %d, %Y %H:%M:%S"),
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
    import os
    import shutil
    import yaml
    from configuration import Configuration

    # Parse and check the new config before touching the current one, so a bad
    # request can't leave the Pi without a usable config.yaml.
    try:
        cfg = yaml.safe_load(request.data)
    except yaml.YAMLError as exc:
        return jsonify({"Success": False, "error": "Invalid YAML: {}".format(exc)}), 400
    if not isinstance(cfg, dict):
        return jsonify({"Success": False, "error": "Config must be a YAML mapping"}), 400
    missing = [c for c in Configuration.REQUIRED_CONFIGS if c not in cfg]
    api = cfg.get("api_server")
    if not isinstance(api, dict):
        missing.append("api_server")
    else:
        missing += ["api_server." + c for c in _REQUIRED_CONFIGS if c not in api]
    if missing:
        return jsonify({"Success": False, "error": "Missing required config: " + ", ".join(missing)}), 400

    # Keep the current config as config.yaml.previous, then swap the new one in atomically.
    if os.path.exists("config.yaml"):
        shutil.copy2("config.yaml", "config.yaml.previous")
    with builtins.open("config.yaml.new", "w") as f:
        yaml.safe_dump(cfg, f)
    os.replace("config.yaml.new", "config.yaml")
    restart()
    return jsonify({"Success": True})
