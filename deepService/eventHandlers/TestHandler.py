# coding: utf-8
from EventHandler import EventHandler

class TestHandler(EventHandler):

    def addEvent(self, objName, eStatus):
        print '*************** TestHandler added: ' + str(objName)

    def delEvent(self, objName, eStatus):
        print 'test del'

    def modifEvent(self, objName, eStatus):
        print 'test modify'

    def errorEvent(self, objName, eStatus):
        print 'test error'
