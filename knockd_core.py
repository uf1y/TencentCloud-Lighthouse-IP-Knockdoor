#!/us/bin/python
# coding:utf-8
# https://cloud.tencent.com/document/sdk/Python
# https://console.cloud.tencent.com/api/explorer?Product=lighthouse&Version=2020-03-24&Action=DeleteFirewallRules&SignVersion=
# https://console.cloud.tencent.com/api/explorer?Product=vpc&Version=2017-03-12&Action=CreateSecurityGroupPolicies&SignVersion=
# pip install --upgrade tencentcloud-sdk-python
# from operator import mod
# from xml.dom.minidom import TypeInfo
import tornado.ioloop
import tornado.web

import json
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.vpc.v20170312 import vpc_client, models
from tencentcloud.lighthouse.v20200324 import lighthouse_client, models as models_light

import time
import datetime
import logging

import os
from dotenv import load_dotenv
load_dotenv(verbose=True)

class LightHouse(object):
    """
    轻量级主机敲门
    """
    _days_rule_expires = int(os.getenv('DAYS_RULE_EXPIRES', '30'))
    _end_point = "lighthouse.tencentcloudapi.com"
    _region = 'ap-shanghai'
    def __init__(self, instance_id, secret_id, secret_key):
        self.instance_id = instance_id
        cred = credential.Credential(secret_id, secret_key)
        
        httpProfile = HttpProfile()
        httpProfile.endpoint = self._end_point

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        self.client = lighthouse_client.LighthouseClient(cred, self._region, clientProfile)

    """
    获取防火墙规则集，类型：FirewallRuleSet
    [{"AppType": "自定义", "Protocol": "TCP", "Port": "8024", "CidrBlock": "183.160.28.85", "Action": "ACCEPT", "FirewallRuleDescription": "NPS-HFCH-MBA-20221102"}]
    """
    def get_fw_polices(self):
        rules = []
        req = models_light.DescribeFirewallRulesRequest()
        params = {
            "InstanceId":  self.instance_id,
            "Limit": 100
        }
        req.from_json_string(json.dumps(params))
        try:
            resp = self.client.DescribeFirewallRules(req)
            rules = resp.FirewallRuleSet
        except TencentCloudSDKException as err:
            logging.info(err)
        return rules

    # 返回要删除的防火墙规则集， N天前的
    def get_knockd_rules_to_delete(self, days=30):
        rules = self.get_fw_polices()
        logging.info('{0} rules found...'.format(len(rules)))
        rules_to_delete = rules.copy()
        logging.info((type(rules_to_delete),type(rules_to_delete[0])))
        for rrule in rules:
            rule = json.loads(rrule.to_json_string())
            desc = rule['FirewallRuleDescription']
            rule_name_prefix = os.getenv('FW_RULE_NAME_PREFIX', 'Mixed-')
            if '@@' in desc and desc.startswith(rule_name_prefix):
                try:
                    day = datetime.datetime.now() - datetime.timedelta(days=days)
                    before_n_day = int(datetime.datetime(day.year, day.month, day.day).strftime('%Y%m%d'))
                    rule_day = int(desc.split('@@')[-1])
                    # Policy created day is bigger than N days before, not to delete, we remove it
                    if rule_day > before_n_day:
                        index_not_to_delete = rules_to_delete.index(rrule)
                        rules_to_delete.pop(index_not_to_delete)
                    else:
                        pass
                except Exception as e:
                    logging.error(e)
            else:
                rules_to_delete.remove(rrule)
        logging.info('{0} rules to delete...'.format(len(rules_to_delete)))
        logging.info(rules_to_delete)
        return rules_to_delete


    def clear_knockd_rules(self, days=30):
        """
        清除满足条件且过期的防火墙规则，默认清楚30天以前的。
        """
        logging.info('clear_knockd_rules()')
        firewall_rules = self.get_knockd_rules_to_delete(days)
        if len(firewall_rules) == 0:
            return
        logging.info('--Rules to be deleted--')
        logging.info(firewall_rules)
        params = {
            "InstanceId": self.instance_id,
            "FirewallRules": json.loads(str(firewall_rules))
        }
        try:
            req = models_light.DeleteFirewallRulesRequest()
            req.from_json_string(json.dumps(params))
            resp = self.client.DeleteFirewallRules(req)
            logging.info(resp)
        except Exception as e:
            logging.error(e)

    # def add_knock_ip(self, instance_id, knocking_ip, port='8888', protocol='TCP', action='ACCEPT', descrption=''):
    def add_knock_ip(self, knocking_ip='127.0.0.1', port='22', protocol='TCP', action='ACCEPT', descrption=''):
        """
        根据敲门的IP和端口，创建防火墙放行规则。
        """
        msg = 'OK'
        if knocking_ip == '127.0.0.1':
            return msg
        try:
            req = models_light.CreateFirewallRulesRequest()
            params = {
                "InstanceId": self.instance_id,
                "FirewallRules": [
                    {
                        "Protocol": protocol,
                        "Port": port,
                        "CidrBlock": knocking_ip,
                        "Action": action,
                        "FirewallRuleDescription": descrption + "@@" + time.strftime('%Y%m%d',time.localtime())
                    }
                ]
            }
            req.from_json_string(json.dumps(params))

            resp = self.client.CreateFirewallRules(req)
            if '{"RequestId":' in str(resp)  and '"Error"' not in str(resp):
                msg = "OK"
                self.clear_knockd_rules(self._days_rule_expires)
            else:
                msg = resp
        except TencentCloudSDKException as err:
            """
            LimitExceeded.FirewallRulesLimitExceeded
            InvalidParameter.FirewallRulesExist 
            LimitExceeded.FirewallRulesLimitExceeded message:当前配额不足，无法创建新的防火墙规则。 
            ResourceNotFound.FirewallRulesNotFound message:未查询到防火墙规则
            """
            if err.code == 'LimitExceeded.FirewallRulesLimitExceeded':
                # pass
                self.clear_knockd_rules(2)
            logging.error(err)
        logging.info(msg)
        return msg