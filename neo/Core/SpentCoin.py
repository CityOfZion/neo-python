# -*- coding:utf-8 -*-


class SpentCoin(object):
    Output = None
    StartHeight = None
    EndHeight = None

    def __init__(self, output, start_height, end_height):
        self.Output = output
        self.StartHeight = start_height
        self.EndHeight = end_height

    def Value(self):
        return self.Output.Value