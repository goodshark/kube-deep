# coding: utf-8
from EventHandler import EventHandler
from util.ApiConfiger import ApiConfig
from util.RedisHelper import RedisHelper
import re

class UpdateJobHandler(EventHandler):

    '''
    tf-3e8f3702-d10b-11e8-abe4-fa163ef8da8a-ps-0-1
    {3e8f3702-d10b-11e8-abe4-fa163ef8da8a-1: 0}
    tf-3e8f3702-d10b-11e8-abe4-fa163ef8da8a-worker-0-3
    {3e8f3702-d10b-11e8-abe4-fa163ef8da8a-3: 0}
    '''
    def modifEvent(self, objName, eStatus):
        print '*************** UpdateJobHandler: ' + str(objName)
        rc = RedisHelper().getRedis()
        psPt = "tf-([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})-ps-([0-9].*)-([0-9].*)"
        res = re.match(psPt, objName)
        if res:
            psKey = res.group(1) + '-' + res.group(3)
            rc.hincrby(ApiConfig().get("event", "ps_key"), psKey, 1)
        else:
            workerPt = "tf-([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})-worker-([0-9].*)-([0-9].*)"
            res = re.match(workerPt, objName)
            if not res:
                return
            if eStatus.succeeded and eStatus.succeeded == 1:
                workerKey = res.group(1) + '-' + res.group(3)
                rc.hincrby(ApiConfig().get("event", "worker_key"), workerKey, 1)
            # TODO check if all worker ready
