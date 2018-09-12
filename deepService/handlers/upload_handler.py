# coding: utf-8
import tornado
from tornado.httpclient import AsyncHTTPClient, HTTPClient, HTTPRequest
from util.ApiConfiger import ApiConfig

class UploadHandler(tornado.web.RequestHandler):
    def get(self, p1="", p2=""):
        pass

    def on_response(self, response):
        print response

    @tornado.web.asynchronous
    def post(self, path):
        print "POST"
        print "path: " + path
        print "file: " + str(self.request.body)
        suffix = "?op=CREATE&user.name={0}&data=true".format(ApiConfig().get("request", "hdfs_user"))
        fullUrl = ApiConfig().get("request", "hdfs_url") + "/" + path + suffix
        print 'url: ' + fullUrl
        header = {
                   "Content-Type": "application/octet-stream"
                 }
        #suffix = "?op=CREATE&user.name={0}&data=true".format()
        #fullUrl = ApiConfig().get("request", "hdfs_url") + "/" + path + suffix
        request = HTTPRequest(url=fullUrl,
                method="PUT",
                headers=header,
                body=self.request.body,
                request_timeout=ApiConfig().getint("request", "timeout"))
        client = AsyncHTTPClient()
        client.fetch(request, self.on_response)
        self.finish()
