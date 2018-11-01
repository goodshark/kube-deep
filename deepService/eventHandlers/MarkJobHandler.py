# coding: utf-8
from EventHandler import EventHandler
from util.ApiConfiger import ApiConfig
from util.RedisHelper import RedisHelper
import re

class MarkJobHandler(EventHandler):

    '''
    tf-3e8f3702-d10b-11e8-abe4-fa163ef8da8a-ps-0-1
    '''
    def addEvent(self, objName, eStatus):
        print '*************** MarkJobHandler: ' + str(objName)
        rc = RedisHelper().getRedis()
        psPt = "tf-([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})-ps-([0-9].*)-([0-9].*)"
        res = re.match(psPt, objName)
        if res:
            psKey = res.group(1) + '-' + res.group(3)
            rc.hsetnx(ApiConfig().get("event", "ps_key"), psKey, 0)
        else:
            workerPt = "tf-([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})-worker-([0-9].*)-([0-9].*)"
            res = re.match(workerPt, objName)
            if not res:
                return
            workerKey = res.group(1) + '-' + res.group(3)
            rc.hsetnx(ApiConfig().get("event", "worker_key"), workerKey, 0)
