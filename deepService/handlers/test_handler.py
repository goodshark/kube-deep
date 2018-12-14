# coding: utf-8
import tornado
import json
import uuid
import base64
from util.ApiConfiger import ApiConfig
from util.RedisHelper import RedisHelper
from util.tool import need_auth
import kubernetes
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import logging
import traceback

def require_basic_auth(handler_class):
    def wrap_execute(handler_execute):
        def require_basic_auth(handler, kwargs):
            print '=== handler: ' + str(handler)
            print '=== kwargs: ' + str(kwargs)
            auth_header = handler.request.headers.get('Authorization')
            if auth_header is None or not auth_header.startswith('Basic '):
                print '=== auth is None or no Basic start'
                handler.set_status(401)
                handler.set_header('WWW-Authenticate', 'Basic realm=Restricted')
                handler._transforms = []
                handler.finish()
                return False
            auth_decoded = base64.decodestring(auth_header[6:])
            kwargs['basicauth_user'], kwargs['basicauth_pass'] = auth_decoded.split(':', 2)
            print '=== auth success ..., start _execute'
            return True
        def _execute(self, transforms, *args, **kwargs):
            if not require_basic_auth(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)
        return _execute

    print 'start wrap handler _execute ......'
    inner_execute = handler_class._execute
    handler_class._execute = wrap_execute(inner_execute)
    print 'wrap handler _execute done ......'
    return handler_class

def method_auth(func):
    def wrapper(*args, **kwargs):
        def verify_auth(headers):
            print 'get auth head'
            print dir(headers)
            print headers
            authInfo = headers.get('Authorization', None)
            if authInfo is None or not authInfo.startswith('Basic '):
                return False
            print authInfo
            authDecoded = base64.decodestring(authInfo[6:])
            username, passwd = authDecoded.split(":")
            print username, passwd
            return True
        handler = None
        if len(args) > 0 and isinstance(args[0], tornado.web.RequestHandler):
            print 'yes, got handler cls'
            handler = args[0]
            print '\n'
            print '='*10
            print handler.request.headers
            print '='*10
            print '\n'
            if not verify_auth(handler.request.headers):
                return False
        else:
            print 'no handler cls'
            return False
        print 'real func ......'
        return func(*args, **kwargs)
    return wrapper

class TestHandler(tornado.web.RequestHandler):

    def get_current_user(self):
        return self.get_secure_cookie("good")

    #@tornado.web.authenticated
    @need_auth
    def get(self):
        print self
        print type(self)
        print id(self)
        print 'username: ' + self.basicUsername
        logging.info('GET stub')
        self.write("good")
        #self.finish()
        #self.write("good")

    def post(self):
        try:
            print self.request.body
            data = json.loads(self.request.body)
            name = data.get("name", "foo")
            if name == "good":
                self.set_secure_cookie(name, "test")
        except:
            traceback.print_exc()

    def get2(self):
        cookie = self.get_secure_cookie("count")
        count = int(cookie) + 1 if cookie else 1
        self.set_secure_cookie("count", str(count))
        self.write("count: " + str(count))
