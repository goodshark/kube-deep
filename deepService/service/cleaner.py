# coding: utf-8
from util.RedisHelper import RedisHelper
from util.ApiConfiger import ApiConfig
import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import json
import traceback

class Cleaner(object):
    def getJobInfo(self):
        configuration = kubernetes.client.Configuration()
        api_instance = kubernetes.client.BatchV1Api(kubernetes.client.ApiClient(configuration))
        namespace = 'default'
        try: 
            api_response = api_instance.list_namespaced_job(namespace)
            return api_response
        except ApiException as e:
            print("Exception when calling BatchV1Api->list_namespaced_job: %s\n" % e)

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
            for ps in psNames:
                delJobInstance.delete_namespaced_job(ps, namespace, body)
                delSvcInstance.delete_namespaced_service(ps, namespace, body)

    def checkJobs(self, jobInfo):
        successUids = []
        failedUids = []
        rc = RedisHelper().getRedis()
        runningSets = rc.smembers(ApiConfig().get("redis", "running_set"))
        for info in jobInfo.items:
            uid = "-".join(info.metadata.name.split('-')[1:-3])
            if uid not in runningSets:
                continue
            failedCount = info.status.failed
            succeedCount = info.status.succeeded
            uidJs = rc.get(uid)
            if not uidJs:
                continue
            uidDetail = json.loads(uidJs)
            if not succeedCount and succeedCount == 1:
                if "success" not in uidDetail:
                    uidDetail["success"] = set()
                uidDetail["success"].add(info.metadata.name)
                rc.set(uid, json.dumps(uidDetail))
            else:
                if not failedCount and failedCount >= 1:
                    if "failed" not in uidDetail:
                        uidDetail["failed"] = set()
                    uidDetail["failed"].add(info.metadata.name)

        for uid in runningSets:
            uidJs = rc.get(uid)
            if not uidJs:
                continue
            uidDetail = json.loads(uidJs)
            runningJobs = uidDetail.get("worker")
            successJobs = uidDetail.get("success", set())
            failedJobs = uidDetail.get("failed", set())
            if len(runningJobs) == len(successJobs):
                successUids.append(uid)
            else if len(failedJobs) >= 1:
                failedUids.append(uid)
        return successUids, failedUids


    def run(self):
        config.load_kube_config()
        while True:
            try:
                jobInfo = self.getJobInfo()
                successJobs, failedJobs = self.checkJobs(jobInfo)
                self.removePs(successJobs)
            except:
                traceback.print_exc()


if __name__ == '__main__':
    cleaner = Cleaner()
    cleaner.run()
