import yaml
from yaml.loader import FullLoader


class Configuration():
    REQUIRED_CONFIGS = ["latitude", "longitude",
                        "sunrise_offset", "sunset_offset", "open_pin", "close_pin"]

    def __init__(self, config_file="config.yaml"):
        with open(config_file, "r") as yml:
            cfg = yaml.load(yml, Loader=FullLoader)
            for c in self.REQUIRED_CONFIGS:
                if c not in cfg:
                    print(c)
                    raise Exception("Missing required config '{}'".format(c))
        self.__dict__.update(cfg)
