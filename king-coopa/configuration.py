import yaml


class Configuration():
    REQUIRED_CONFIGS = ["actuator_specs", "close_pin", "latitude",
                        "longitude", "open_pin", "sunrise_offset", "sunset_offset"]

    def __init__(self, config_file="config.yaml"):
        with open(config_file, "r") as yml:
            cfg = yaml.safe_load(yml)
            for c in self.REQUIRED_CONFIGS:
                if c not in cfg:
                    raise Exception("Missing required config '{}'".format(c))
        self.__dict__.update(cfg)

    def serializable(self):
        return self.__dict__
