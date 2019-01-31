import json

class Config():

    def __init__(self, ch):
        f = open("./config.json", 'r')
        s = f.read()
        c_dict = json.loads(s)[ch]
        # converting a dictionary into an object 
        from collections import namedtuple
        self.config  = namedtuple("Conf", c_dict.keys())(*c_dict.values())
        print self.config

    def get(self):
        return self.config
