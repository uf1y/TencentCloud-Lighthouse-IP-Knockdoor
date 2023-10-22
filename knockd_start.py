# coding:utf8
import tornado.ioloop
import tornado.web
import re
import os

import logging
logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("log.txt")
handler.setLevel(logging.INFO)
logger.addHandler(handler)

from dotenv import load_dotenv
load_dotenv(verbose=True)

from knockd_core import LightHouse

# --LOAD--ENV--
MESSAGE_SUCCESS = os.getenv('MESSAGE_SUCCESS')
MESSAGE_FAILURE = os.getenv('MESSAGE_FAILURE')

KNOCK_REFERER = os.getenv('KNOCK_REFERER')

FW_PERMIT_PORTS = os.getenv('FW_PERMIT_PORTS')
LIGHTHOUSE_INSTANCE_IDS = os.getenv('LIGHTHOUSE_INSTANCE_IDS')
KNOCK_REQUEST_PATH = os.getenv('KNOCK_REQUEST_PATH')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_status(500)
        self.write(MESSAGE_FAILURE)

class KnockdoorHandler(tornado.web.RequestHandler):
    def get(self):
        # 当前服务器看到的真实远程IP地址，默认方式
        knocking_ip = self.request.remote_ip
        method_to_get_client_ip  = os.getenv('METHOD_TO_GET_CLIENT_IP', "1")
        if "3" == method_to_get_client_ip:
            # 客户端主动携带的IP地址，不安全，容易被篡改
            knocking_ip = self.request.headers.get('ip', '127.0.0.1')
        elif "2" == method_to_get_client_ip:
            # 支持Cloudflared代理的原始IP地址，但CF看到的IP地址可能不是真实IP地址
            # CN网内各种奇葩的广电、华数字的路由和NAT策略会让你疯掉
            knocking_ip = self.request.headers.get("X-Real-IP") or \
                self.request.headers.get("X-Forwarded-For") or \
                    self.request.remote_ip

        logging.info(f"Knocking from client:{knocking_ip}")
        self.set_status(500)
        if re.match(r"\d+\.\d+\.\d+\.\d+", knocking_ip):
            if self.knock_lighthouse(knocking_ip):
                self.write(MESSAGE_SUCCESS)
                return
        self.write(MESSAGE_FAILURE)

    def knock_lighthouse(self, knocking_ip='127.0.0.1'):
        """
        敲门lighthouse
        """
        client = self.request.headers.get('Location', 'DEFAULT')
        referer = self.request.headers.get('Referer', '-')
        if referer == KNOCK_REFERER:
            desc = "Knockd-" +  client
            instance_ids = os.getenv('TENCENT_CLOUD_LIGHTHOUSE_INSTANCE_IDS').strip().strip(',').strip().split(',')
            secret_id = os.getenv('TENCENT_CLOUD_SECRET_ID')
            secret_key = os.getenv('TENCENT_CLOUD_SECRET_KEY')
            # 每一个轻量级主机实例，单独处理
            for instance_id in instance_ids:
                if instance_id == '':continue
                tcp_ports = os.getenv('FW_PERMIT_PORTS_TCP').strip().strip(',').strip()
                tcp_ports = ','.join(tcp_ports.split(','))
                udp_ports = os.getenv('FW_PERMIT_PORTS_UDP').strip().strip(',').strip()
                udp_ports = ','.join(udp_ports.split(','))
                # 先处理TCP，后处理UDP
                if tcp_ports != '' and tcp_ports != ',':
                    LightHouse(instance_id, secret_id, secret_key).add_knock_ip(knocking_ip, tcp_ports, 'TCP', descrption=desc)
                if udp_ports != '' and udp_ports != ',':
                    LightHouse(instance_id, secret_id, secret_key).add_knock_ip(knocking_ip, udp_ports, 'UDP', descrption=desc)
            return True
        return False

"""A Knockd web service"""
def knockdoor_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (KNOCK_REQUEST_PATH, KnockdoorHandler)
    ])

if __name__ == '__main__':
    app = knockdoor_app()
    int_bind_port = int(os.getenv('BIND_PORT', "8080"))
    str_bind_ip = os.getenv('BIND_IP', "0.0.0.0")
    app.listen(int_bind_port, str_bind_ip)
    tornado.ioloop.IOLoop.current().start()