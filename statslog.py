#!/usr/bin/env python

import logging
import os

"""
This class provides func to log individual's stat reports individual's log file under logs dir.
"""

class StatsLog(object):
    formatter = '%(asctime)s %(name)-12s %(message)s'
    datefmt = '%m-%d %H:%M'

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG, format=StatsLog.formatter, datefmt=StatsLog.datefmt)
        self.logRootDir = os.getcwd() + '/logs/'
        self.consolelogger = logging.getLogger()  # get the root logger

    def logConsole(self, text):
        self.consolelogger.setLevel(logging.DEBUG)
        self.consolelogger.propagate = False
        self.consolelogger.debug(text)

    def getLogFileHandler(self, name, level=logging.DEBUG):
        handler = logging.FileHandler(self.logRootDir + name)
        handler.setLevel(level)
        formatter = logging.Formatter(fmt=StatsLog.formatter, datefmt=StatsLog.datefmt)
        handler.setFormatter(formatter)
        return handler

    def logFile(self, name, text):
        self.stafflogger = logging.getLogger(name)
        staffhandler = self.getLogFileHandler(name)
        self.stafflogger.addHandler(staffhandler)
        #self.stafflogger.propagate = False    # prevent from propagate to upper logger(console)
        self.stafflogger.debug(text)
        self.stafflogger.removeHandler(staffhandler)

''' unit test '''
def unitTest():
    slog = StatsLog()
    slog.logConsole('hello world')
    slog.logFile('haijin', 'hello world')

if __name__ == '__main__':
    unitTest()

