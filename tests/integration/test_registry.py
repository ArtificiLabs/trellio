# import multiprocessing
#
# import requests
#
# from trellio import Host, HTTPService, TCPService, TCPServiceClient
# from trellio import request, get, Response, api
# from trellio.registry import Registry, Repository
#
# processes = []
#
#
# class ServiceC(HTTPService):
#     def __init__(self, host, port):
#         super().__init__("ServiceC", 1, host, port)
#
#     @get(path="/{data}")
#     def get_echo(self, request):
#         return Response(status=200, body='blah'.encode())
#
#
# class ServiceA(TCPService):
#     def __init__(self, host, port):
#         super().__init__("ServiceA", 1, host, port)
#
#     @api
#     def echo(self, data):
#         return data
#
#
# class ServiceClientA(TCPServiceClient):
#     def __init__(self):
#         super().__init__("ServiceA", 1)
#
#     @request
#     def echo(self, data):
#         return locals()
#
#
# class ServiceB(HTTPService):
#     def __init__(self, host, port, client_a):
#         self._client_a = client_a
#         super().__init__("ServiceB", 1, host, port)
#
#     @get(path="/{data}")
#     async def get_echo(self, request):
#         data = request.match_info.get('data')
#         d = await self._client_a.echo(data)
#         return Response(status=200, body=d.encode())
#
#
# def start_registry():
#     repository = Repository()
#     registry = Registry(None, 4500, repository)
#     registry.start()
#
#
# def start_servicea():
#     service_a = ServiceA(host='0.0.0.0', port=8001)
#     Host.configure()
#     Host.attach_tcp_service(service_a)
#     Host.run()
#
#
# def start_serviceb():
#     client_a = ServiceClientA()
#     service_b = ServiceB(host='0.0.0.0', port=4503, client_a=client_a)
#     service_b.clients = [client_a]
#     Host.configure(registry_host='127.0.0.1', registry_port=4500,
#                    pubsub_host='127.0.0.1', pubsub_port=6379, service_name='serviceb')
#
#     Host.attach_http_service(service_b)
#     Host.run()
#
#
# def setup_module():
#     global processes
#     for target in [start_servicea, start_serviceb]:
#         p = multiprocessing.Process(target=target)
#         p.start()
#         processes.append(p)
#
#     # allow the subsystems to start up.
#     # sleep for awhile
#     import time
#     time.sleep(5)
#
#
# def teardown_module():
#     for p in processes:
#         p.terminate()
#
#
# def test_service_b():
#     url = 'http://127.0.0.1:4503/blah'
#     r = requests.get(url)
#     assert r.text == 'blah'
#     assert r.status_code == 200
#
#
# if __name__ == "__main__":
#     setup_module()
from aiohttp.web_response import Response

from trellio import Host, HTTPService, get, TCPServiceClient, request
from trellio.services import TCPService, api


class TestTCPClient(TCPServiceClient):
    def __init__(self):
        super(TestTCPClient, self).__init__('test_service', '1')

    @request
    def echo(self, q):
        return locals()


class TestHTTPServiceA(HTTPService):
    def __init__(self):
        super(TestHTTPServiceA, self).__init__('test_service_a', '1')
        self._client = TestTCPClient()

    @get(path='/')
    async def echo(self, request):
        resp = await self._client.echo(request.GET.get('q'))
        return Response(body=resp)


class TestTCPService(TCPService):
    def __init__(self):
        super(TestTCPService, self).__init__('test_service_a', '1')

    @api
    async def echo(self):
        return "echo"


if __name__ == "__main__":
    tcp_service = TestTCPService()
    http_service = TestHTTPServiceA()
    Host.configure(host_name='test_service_a', http_port=8002, tcp_port=8003, workers=4)
    Host.attach_service(http_service)
    Host.attach_tcp_service(tcp_service)
    tcp_service.clients = [TestTCPClient()]
    Host.run()
