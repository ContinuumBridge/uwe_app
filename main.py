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
ModuleName         = "uwe_app" 
START_DELAY        = 20          # Delay before start of sending dummy data
DATA_SEND_INTERVAL = 20          # How often to send dummy data

import sys
import os.path
import time
import logging
from peewee import FloatField
from cbcommslib import CbApp, DataStore, DataModel
from cbconfig import *
from twisted.internet import reactor

class TemperatureData(DataModel):
    temperature = FloatField()

class UWEApp(CbApp):

    def __init__(self, argv):

        self.store = DataStore()
        self.store.register(TemperatureData)

        logging.basicConfig(filename=CB_LOGFILE,level=CB_LOGGING_LEVEL,format='%(asctime)s %(message)s')
        self.appClass = "control"
        self.state = "stopped"
        self.sensorID = ""
        self.switchID = ""
        #CbApp.__init__ MUST be called
        CbApp.__init__(self, argv)

    # Should put in library
    def isotime(self):
        t = time.time()
        gmtime = time.gmtime(t)
        milliseconds = '%03d' % int((t - int(t)) * 1000)
        now = time.strftime('%Y-%m-%dT%H:%M:%S.', gmtime) + milliseconds +"Z"
        return now

    def setState(self, action):
        self.state = action
        msg = {"id": self.id,
               "status": "state",
               "state": self.state}
        self.sendManagerMessage(msg)

    def onAdaptorService(self, message):
        for p in message["service"]:
            if p["characteristic"] == "temperature":
                self.sensorID = message["id"]
                req = {"id": self.id,
                       "request": "service",
                       "service": [
                                    {"characteristic": "temperature",
                                     "interval": 30.0}
                                  ]
                      }
                self.sendMessage(req, message["id"])
                logging.debug("%s onadaptorService, req: %s", ModuleName, req)
            elif p["characteristic"] == "switch":
                logging.debug("%s onAdaptorService unexpected device %s", ModuleName, str(message))
        self.setState("running")

    def onAdaptorData(self, message):
        if message["id"] == self.sensorID:
            if message["content"] == "temperature":
                logging.debug("%s %s Temperature = %s", ModuleName, self.id, message["data"])
            else:
                logging.debug("%s Trying to process temperature before switch connected", ModuleName)
        elif message["id"] == self.switchID:
            logging.debug("%s onAdaptorData unexpected device %s", ModuleName, message)

    def sendAppData(self):
        msg = {
               "source": self.id,
               "destination": "CID1",
               "time_sent": self.isotime(),
               "body": {
                        "verb": "post",
                        "data": "dummy",
                        "time": time.time()
                       }
              }    
        logging.debug("%s onAppData sending message: %s", ModuleName, msg)
        self.sendMessage(msg, "conc")
        reactor.callLater(DATA_SEND_INTERVAL, self.sendAppData)

    def onConfigureMessage(self, config):
        self.setState("starting")
        # This is just a botch so that the app will send data without any other interaction
        reactor.callLater(START_DELAY, self.sendAppData)

if __name__ == '__main__':
    UWEApp(sys.argv)
