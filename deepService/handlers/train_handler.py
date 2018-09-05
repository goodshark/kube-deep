# coding: utf-8
import tornado
import json
import uuid
from util.ApiConfiger import ApiConfig
import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException

class TrainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        print 'GET'
        self.finish()

    def parse(self, data):
        return json.loads(data)

    def genV1Service(self, uid, workType, seq, count):
        tfId = "-".join(["tf", uid, workType, str(seq), str(count)])
        body = kubernetes.client.V1Service()
        body.api_version = "v1"
        body.kind = "Service"
        metaBody = kubernetes.client.V1ObjectMeta()
        metaBody.name = tfId
        body.metadata = metaBody
        specBody = kubernetes.client.V1ServiceSpec()
        specBody.cluster_ip = "None"
        specBody.selector = {"tf": tfId}
        portBody = kubernetes.client.V1ServicePort(port=ApiConfig().getint("k8s", "headless_port"))
        portBody.target_port = ApiConfig().getint("k8s", "headless_port")
        specBody.ports = [portBody]
        body.spec = specBody
        return body

    def createService(self, uid, runInfo):
        config.load_kube_config()
        configuration = kubernetes.client.Configuration()
        api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))
        namespace = 'default'
        for workType in runInfo:
            workCount = runInfo.get(workType, 1)
            for i in xrange(workCount):
                body = self.genV1Service(uid, workType, i, workCount)
                print body
                try:
                    print '='*10 
                    api_response = api_instance.create_namespaced_service(namespace, body)
                    print api_response
                except ApiException as e:
                    print("Exception when calling CoreV1Api->create_namespaced_service: %s\n" % e)
                    raise

    def deleteService(self):
        pass

    def genV1Job(self, uid, workType, seq, count, info, ps, workers):
        tfId = "-".join(["tf", str(uid), workType, str(seq), str(count)])
        body = kubernetes.client.V1Job()
        body.api_version = "batch/v1"
        body.kind = "Job"
        metaBody = kubernetes.client.V1ObjectMeta()
        metaBody.name = tfId
        body.metadata = metaBody

        tempSpec = kubernetes.client.V1PodTemplateSpec()
        tempMetaBody = kubernetes.client.V1ObjectMeta()
        tempMetaBody.name = tfId
        tempMetaBody.labels = {"tf": tfId}
        tempSpec.metadata = tempMetaBody
        containerBody = kubernetes.client.V1Container(name=tfId)
        tempInnerSpec = kubernetes.client.V1PodSpec(containers=[containerBody])
        tempInnerSpec.restart_policy = "Never"
        #tempInnerSpec.containers = [containerBody]
        #containerBody.name = tfId
        containerBody.image = ApiConfig().get("image", "tensorflow")
        containerBody.command = ["/notebooks/entry.sh", info.get("file", ""), ps, workers, workType, str(seq), info.get("data", "/notebooks")]
        portBody = kubernetes.client.V1ContainerPort(ApiConfig().getint("k8s", "headless_port"))
        containerBody.ports = [portBody]
        tempSpec.spec = tempInnerSpec
        specBody = kubernetes.client.V1JobSpec(template=tempSpec)
        body.spec = specBody
        return body
        

    def createJob(self, uid, info):
        configuration = kubernetes.client.Configuration()
        api_instance = kubernetes.client.BatchV1Api(kubernetes.client.ApiClient(configuration))
        runInfo = info.get("detail", None)
        ps_count = runInfo.get("ps", 0)
        worker_count = runInfo.get("worker", 0)
        svcPort = ApiConfig().get("k8s", "headless_port")
        ps_hosts = ["-".join(["tf", str(uid), "ps", str(i), str(ps_count)])+":"+svcPort for i in xrange(ps_count)]
        worker_hosts = ["-".join(["tf", str(uid), "worker", str(i), str(worker_count)])+":"+svcPort for i in xrange(worker_count)]
        print "ps: " + str(ps_hosts)
        print "worker: " + str(worker_hosts)
        for workType in runInfo:
            count = runInfo.get(workType, 1)
            for i in xrange(count):
                try:
                    body = self.genV1Job(uid, workType, i, count, info, ",".join(ps_hosts), ",".join(worker_hosts))
                    print body
                    namespace = ApiConfig().get("namespace", info.get("type", "tensorflow"))
                    api_response = api_instance.create_namespaced_job(namespace, body)
                    print api_response
                except ApiException as e:
                    print("Exception when calling BatchV1Api->create_namespaced_job: %s\n" % e)
                    raise


    def deleteJob(self):
        pass

    def deletePsPod(self):
        pass

    def submit(self, info):
        '''
        headless service
        job // dns
        '''
        uid = uuid.uuid1()
        self.createService(str(uid), info["detail"])
        self.createJob(uid, info)
        # TODO enqueue delete svc

    @tornado.web.asynchronous
    def post(self):
        print "POST"
        info = self.parse(self.request.body)
        print info
        self.submit(info)
        self.finish()
