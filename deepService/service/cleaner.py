# coding: utf-8
from __future__ import print_function
import sys
import os
sys.path.append(os.path.split(os.path.realpath(__file__))[0]+"/..")
from util.RedisHelper import RedisHelper
from util.ApiConfiger import ApiConfig
import kubernetes
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from multiprocessing import Pool
import time
import json
import importlib
import traceback


class Cleaner(object):
    def __init__(self):
        self.eventHandlers = []

    def getJobInfo(self):
        configuration = kubernetes.client.Configuration()
        api_instance = kubernetes.client.BatchV1Api(kubernetes.client.ApiClient(configuration))
        namespace = 'default'
        try: 
            api_response = api_instance.list_namespaced_job(namespace)
            return api_response
        except ApiException as e:
            print("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)

    def moveUid(self, uid):
        rc = RedisHelper().getRedis()
        rc.smove(ApiConfig().get("redis", "running_set"),
                ApiConfig().get("redis", "success_set"),
                uid)

    def removePs(self, uids):
        configuration = kubernetes.client.Configuration()
        delJobInstance = kubernetes.client.BatchV1Api(kubernetes.client.ApiClient(configuration))
        delSvcInstance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))
        rc = RedisHelper().getRedis()
        for uid in uids:
            uidJs = rc.get(uid)
            if not uidJs:
                continue
            uidDetail = json.loads(uidJs)
            psNames = uidDetail.get("ps", [])
            namespace = 'default'
            body = kubernetes.client.V1DeleteOptions()
            body.propagation_policy = 'Foreground'
            for fullPs in psNames:
                ps = fullPs.split(":")[0]
                print('delete ps ' + ps + ' ......')
                try:
                    delJobInstance.delete_namespaced_job(ps, namespace, body)
                    delSvcInstance.delete_namespaced_service(ps, namespace, body)
                    self.moveUid(uid)
                except:
                    traceback.print_exc()

    def checkJobs(self, jobInfo):
        successUids = []
        failedUids = []
        rc = RedisHelper().getRedis()
        runningSets = rc.smembers(ApiConfig().get("redis", "running_set"))
        for info in jobInfo.items:
            uid = "-".join(info.metadata.name.split('-')[1:-3])
            print("make uid: " + str(uid))
            if uid not in runningSets:
                continue
            failedCount = info.status.failed
            succeedCount = info.status.succeeded
            uidJs = rc.get(uid)
            print('failedCount: ' + str(failedCount))
            print('succeedCount: ' + str(succeedCount))
            print('type: ' + str(type(succeedCount)))
            print('uidjs: ' + uidJs)
            if not uidJs:
                continue
            uidDetail = json.loads(uidJs)
            print('detail: ' + str(uidDetail))
            if succeedCount and succeedCount == 1:
                print('success done')
                if "success" not in uidDetail:
                    uidDetail["success"] = []
                if info.metadata.name not in uidDetail["success"]:
                    uidDetail["success"].append(info.metadata.name)
                rc.set(uid, json.dumps(uidDetail))
            else:
                print('failed done')
                if failedCount and failedCount >= 1:
                    if "failed" not in uidDetail:
                        uidDetail["failed"] = []
                    if info.metadata.name not in uidDetail["failed"]:
                        uidDetail["failed"].append(info.metadata.name)

        for uid in runningSets:
            uidJs = rc.get(uid)
            if not uidJs:
                continue
            uidDetail = json.loads(uidJs)
            runningJobs = uidDetail.get("worker")
            successJobs = uidDetail.get("success", [])
            failedJobs = uidDetail.get("failed", [])
            if len(runningJobs) == len(successJobs):
                successUids.append(uid)
            elif len(failedJobs) >= 1:
                failedUids.append(uid)
        return successUids, failedUids

    def loadHandlers(self):
        handlerStrs = ApiConfig().get("event", "handlers")
        handlerNames = handlerStrs.split(",")
        for name in handlerNames:
            print("name: " + name)
            m = importlib.import_module('eventHandlers.'+name.strip())
            cls = getattr(m, name.strip())
            self.eventHandlers.append(cls())


    def handleEvent(self, event):
        pool = Pool(processes=4) 
        for handler in self.eventHandlers:
            print("=======================================" + str(type(handler)))
            pool.apply_async(handler, [event['type'], event['object'].metadata.name, event['object'].status])

    def watchLoop(self):
        #v1 = client.CoreV1Api()
        v1 = client.BatchV1Api()
        w = watch.Watch()
        events = w.stream(v1.list_namespaced_job, "default", timeout_seconds=0)

        for event in events:
            print("Event: %s, %s, %s" % (event['type'], event['object'].metadata.name, event['object'].status))
            '''
            eventType = event['type']
            eventName = event['object'].metadata.name
            eventStatus = event['object'].status
            '''
            self.handleEvent(event)
        print("done ===============")

    def run(self):
        config.load_kube_config()
        self.loadHandlers()
        self.watchLoop()
        '''
        while True:
            try:
                jobInfo = self.getJobInfo()
                successJobs, failedJobs = self.checkJobs(jobInfo)
                self.removePs(successJobs)
                time.sleep(5)
            except KeyboardInterrupt:
                break
            except:
                traceback.print_exc()
                time.sleep(5)
        '''


if __name__ == '__main__':
    cleaner = Cleaner()
    cleaner.run()
