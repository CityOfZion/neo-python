#!/usr/bin/env python

class Mongo:
    def __init__(self,host='localhost',port=27017,usr=None,pwd=None):
        self.host = host
        self.port = port
        self.usr = usr
        self.pwd = pwd

bcdb = Mongo()

