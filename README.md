# TencentCloud-Lighthouse-IP-Knockdoor
一款针对腾讯轻量应用服务器的IP敲门程序。客户端先敲门，然后Kncod开通Lighthouse的防火墙访问策略。

# 需求场景

## 背景
- 服务端：61.170.71.133，腾讯云轻量应用服务器，但不希望所有人都可以连接它，只对受信任的客户端IP开放特定端口。
- 客户端：83.94.156.180，一个或者多个，经常变换IP

## 需求

客户端向服务端指定端口敲门（请求一个特定的URL），服务端通过腾讯云API，在防火墙上添加客户端IP地址，允许客户端访问其他业务端口。

<img width="60%" alt="image" border="1" src="https://github.com/uf1y/TencentCloud-Lighthouse-IP-Knockdoor/assets/117698857/9df33c47-a05b-42b9-a6d0-176259c4abde">

# 功能阐述

## 服务端主逻辑
- Knockd服务监听在TCP/8080端口；
- Lighthouse防火墙默认开放0.0.0.0/0对TCP/8080的访问
- 客户端敲门请求：http://<TencentCloud_Lighthouse_IP>:8080/favico.ico
- 服务端识别出客户端IP地址和目标服务的端口（通过配置文件自定义），将IP地址添加到腾讯云轻量应用服务器的防火墙

## 客户端使用

### HTTP请求格式

```
GET /favico.ico HTTP/1.1
Host: 61.170.71.133:8080
User-Agent: curl/8.1.2
Accept: */*
Referer:https://www.baidu..com/
Location:Offfice_01
```

### Curl请求方式：
```bash
curl  -H "Referer:https://www.baidu..com/" \
      -H "Location:Offfice_01" \
http://61.170.71.133:8080/favico.ico
```

## 防火墙配置结果

<img width="80%" alt="image" border="1" src="https://github.com/uf1y/TencentCloud-Lighthouse-IP-Knockdoor/assets/117698857/29c6afef-0303-4849-8b74-123944b33930">

# 关键配置文件.env

```ini
# 敲门成功的返回信息
MESSAGE_SUCCESS='500 Internal Server Error.'
# 敲门失败的返回信息
MESSAGE_FAILURE='500 Internal Server Error'

# 防火墙要开通的端口，逗号分隔
# FW_PERMIT_PORTS='22,80,443'
# FW_PERMIT_PORTS='22,'
FW_PERMIT_PORTS_TCP='80，443,3389'
# FW_PERMIT_PORTS_UDP='514,'
FW_PERMIT_PORTS_UDP=''
# 防火墙规则前缀
FW_RULE_NAME_PREFIX='Knockd-'

# 轻量级主机的示例ID，逗号分割
TENCENT_CLOUD_LIGHTHOUSE_INSTANCE_IDS ='lhins-a0ogy7ty,'

# 客户端敲门时HTTP头部自定义的Referer，相当于密钥
KNOCK_REFERER = 'https://www.baidu..com/'

# 敲门请求的URL路径
KNOCK_REQUEST_PATH='/favico.ico'

# 腾讯云API Secret Id和Secret Key
TENCENT_CLOUD_SECRET_ID='AKID*************oSs'
TENCENT_CLOUD_SECRET_KEY='rZ3J*************aP'

# 获取客户端IP地址的方法，默认：1
# 1)实际连接服务器的的IP
# 2)代理服务器给的“真实”IP
# 3)客户端自己声明的IP（不安全）
METHOD_TO_GET_CLIENT_IP="1"

# 防火墙规则有效期
DAYS_RULE_EXPIRES="30"

# 服务监听端口，默认：8080
BIND_PORT="8080"
# 服务绑定IP地址，默认：0.0.0.0
BIND_IP="0.0.0.0"
```

# Knockd服务端安装使用
```bash
# change .env file before running.
python knockd_start.py
```
