# coding: utf-8
import tornado
import json
from util.ApiConfiger import ApiConfig
from kubernetes import client, config
from kubernetes.client.rest import ApiException

class TrainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        pass

    def parse(self, data):
        return json.loads(data)

    def genV1Service(self, workType):
        body = kubernetes.client.V1Service()
        body.api_version = "v1"
        body.kind = "Service"
        metaBody = kubernetes.client.V1ObjectMeta()
        metaBody.name = "abcTODO"
        body.metadata = metaBody
        specBody = kubernetes.client.V1ServiceSpec()
        specBody.cluster_ip = None
        specBody.selector = {"tf": "abcTODO"}
        portBody = kubernetes.client.V1ServicePort()
        portBody.port = ApiConfig().getint("k8s", "headless_port")
        portBody.target_port = ApiConfig().getint("k8s", "headless_port")
        specBody.ports = [portBody]
        body.spec = specBody

    def createService(self, runInfo):
        configuration = kubernetes.client.Configuration()
        api_instance = kubernetes.client.CoreV1Api(kubernetes.client.ApiClient(configuration))
        namespace = 'default'
        for workType in runInfo:
            for i in range(runInfo.get(workType, 1)):
                body = self.genV1Service(workType)
                try:
                    api_response = api_instance.create_namespaced_service(namespace, body)
                    print api_response
                except ApiException as e:
                    print("Exception when calling CoreV1Api->create_namespaced_service: %s\n" % e)
                    raise

    def deleteService(self):
        pass

    def createJob(self, info):
        pass

    def deleteJob(self):
        pass

    def deletePsPod(self):
        pass

    def submit(self, info):
        '''
        headless service
        job // dns
        '''
        self.createService(info["detail"])
        self.createJob(info)

    @tornado.web.asynchronous
    def post(self):
        info = self.parse(self.request.body)
        print info
        self.submit(info)
        self.finish()
