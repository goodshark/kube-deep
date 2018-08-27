# coding: utf-8
import tornado
import json
from kubernetes import client, config

class TrainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        pass

    def parse(self, data):
        return json.loads(data)

    @tornado.web.asynchronous
    def post(self):
        info = self.parse(self.request.body)
        print info
        self.finish()
