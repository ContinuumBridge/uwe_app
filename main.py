#!/usr/bin/env python
# main.py
"""
Copyright (c) 2014 ContinuumBridge Limited

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
ModuleName = "uwe_app" 

import sys
import os.path
import time
import logging
from peewee import FloatField
from cbcommslib import CbApp, DataStore, DataModel
from cbconfig import *

class TemperatureData(DataModel):
    temperature = FloatField()

class UWEApp(CbApp):

    def __init__(self, argv):

        self.store = DataStore()
        self.store.register(TemperatureData)

        logging.basicConfig(filename=CB_LOGFILE,level=CB_LOGGING_LEVEL,format='%(asctime)s %(message)s')
        self.appClass = "control"
        self.state = "stopped"
        self.gotSwitch = False
        self.sensorID = ""
        self.switchID = ""
        # Temporary botch - set temperature from a file
        try:
            tempFile = CB_CONFIG_DIR + 'set-temp'
            with open(tempFile, 'r') as f:
                s = f.read()
            if s.endswith('\n'):
                s = s[:-1]
            SET_TEMP = s
            logging.debug("%s Set temperature: %s", ModuleName, SET_TEMP)
        except:
            logging.debug("%s Could not read set-temp file", ModuleName)
        #CbApp.__init__ MUST be called
        CbApp.__init__(self, argv)

    def setState(self, action):
        self.state = action
        msg = {"id": self.id,
               "status": "state",
               "state": self.state}
        self.sendManagerMessage(msg)

    def onAdaptorFunctions(self, message):
        for p in message["functions"]:
            if p["parameter"] == "temperature":
                self.sensorID = message["id"]
                req = {"id": self.id,
                      "request": "functions",
                      "functions": [
                                    {"parameter": "temperature",
                                    "interval": 30.0}
                                   ]
                      }
                self.sendMessage(req, message["id"])
                logging.debug("%s onadaptorFunctions, req: %s", ModuleName, req)
            elif p["parameter"] == "switch":
                logging.debug("%s onAdaptorFunctions unexpected device %s", ModuleName, str(message))
        self.setState("running")

    def onAdaptorData(self, message):
        if message["id"] == self.sensorID:
            if message["content"] == "temperature":
                logging.debug("%s %s Temperature = %s", ModuleName, self.id, message["data"])
            else:
                logging.debug("%s Trying to process temperature before switch connected", ModuleName)
        elif message["id"] == self.switchID:
            logging.debug("%s onAdaptorData unexpected device %s", ModuleName, message)

    def onConfigureMessage(self, config):
        self.setState("starting")

if __name__ == '__main__':
    app = UWEApp(sys.argv)
