# coding: utf-8
from util.RedisHelper import RedisHelper
from util.ApiConfiger import ApiConfig
import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import traceback

class Cleaner(object):
    def removeSvc(self, svcs):
        pass
    
    def removePs(self, jobs):
        pass

    def checkJobs(self):
        rc = RedisHelper().getRedis()
        runningSets = rc.smembers(ApiConfig().get("redis", "running_set"))
        for uid in runningSets:
            info = rc.get(uid)
            for worker in info.get("worker", []):
                pass

    def run(self):
        while True:
            try:
                finishJobs = self.checkJobs()
                self.removeSvc(finishJobs)
                self.removePs(finishJobs)
            except:
                traceback.print_exc()


if __name__ == '__main__':
    cleaner = Cleaner()
    cleaner.run()
