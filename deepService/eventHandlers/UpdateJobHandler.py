# coding: utf-8
from EventHandler import EventHandler
from util.ApiConfiger import ApiConfig
from util.RedisHelper import RedisHelper
import kubernetes
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
import json
import re
import traceback

class UpdateJobHandler(EventHandler):
    def removePs(self, psList):
        print 'deleting ps list: ' + str(psList)
        # TODO del k8s-ps, del keys
        config.load_kube_config()
        configuration = kubernetes.client.Configuration()
        delJobInstance = kubernetes.client.BatchV1Api(kubernetes.client.ApiClient(configuration))
        delSvcInstance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))
        body = kubernetes.client.V1DeleteOptions()
        body.propagation_policy = 'Foreground'
        namespace = 'default'
        for ps in psList:
            try:
                delJobInstance.delete_namespaced_job(ps, namespace, body)
                delSvcInstance.delete_namespaced_service(ps, namespace, body)
            except:
                traceback.print_exc()

    '''
    tf-3e8f3702-d10b-11e8-abe4-fa163ef8da8a-ps-0-1
    {3e8f3702-d10b-11e8-abe4-fa163ef8da8a-1: 0}
    tf-3e8f3702-d10b-11e8-abe4-fa163ef8da8a-worker-0-3
    {3e8f3702-d10b-11e8-abe4-fa163ef8da8a-3: 0}
    '''
    def modifEvent(self, objName, eStatus):
        print '*************** UpdateJobHandler modify event: ' + str(objName)
        rc = RedisHelper().getRedis()
        psPt = "tf-([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})-ps-([0-9].*)-([0-9].*)"
        res = re.match(psPt, objName)
        if res:
            # ps may be shutdown itself through singal from worker
            print 'ps modified'
            #psKey = res.group(1)
            #rc.hincrby(ApiConfig().get("event", "ps_key"), psKey, -1)
        else:
            workerPt = "tf-([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})-worker-([0-9].*)-([0-9].*)"
            res = re.match(workerPt, objName)
            if not res:
                return
            if eStatus.succeeded and eStatus.succeeded == 1:
                workerKey = res.group(1)
                curCount = rc.hincrby(ApiConfig().get("event", "worker_key"), workerKey, -1)
                if (int(curCount) == 0):
                    print 'prepare delete ps ++++++++++++++++++++++++++++++'
                    psCnt = rc.hget(ApiConfig().get("event", "ps_key"), res.group(1))
                    allPs = ['tf-'+res.group(1)+'-ps-'+str(i)+'-'+psCnt for i in xrange(int(psCnt))]
                    allWorker = ['tf-'+res.group(1)+'-worker-'+str(i)+'-'+res.group(3) for i in xrange(int(res.group(3)))]
                    print 'all ps: ' + str(allPs)
                    print 'all worker: ' + str(allWorker)
                    tfInfo = {'ps': allPs, 'worker': allWorker}
                    rc.rpush(ApiConfig().get("event", "delete_queue"), json.dumps(tfInfo))
                else:
                    print 'one tf worker done successfully ......'
            else:
                # TODO mark failed
                pass

    def delEvent(self, objName, eStatus):
        print '************* UpdateJobHandler delete event: ' + str(objName)
        rc = RedisHelper().getRedis()
        psPt = "tf-([0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12})-ps-([0-9].*)-([0-9].*)"
        res = re.match(psPt, objName)
        if res:
            print 'delete event matched'
            psKey = res.group(1)
            print 'delete event ps_key: ' + psKey
            try:
                psCurCount = rc.hincrby(ApiConfig().get("event", "ps_key"), psKey, -1)
            except:
                print 'got error'
                traceback.print_exc()
            print 'after hincrby ......'
            print 'delete event ps cur count: ' + str(psCurCount)
            if (int(psCurCount) == 0):
                print ''
                rc.hdel(ApiConfig().get("event", "ps_key"), psKey)
                rc.hdel(ApiConfig().get("event", "worker_key"), psKey)
        else:
            print 'del event not matched'
