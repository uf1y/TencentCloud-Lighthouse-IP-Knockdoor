# TencentCloud-Lighthouse-IP-Knockdoor
`腾讯云轻量应用服务器防火墙敲门服务`：一款针对腾讯轻量应用服务器的IP敲门程序。客户端先敲门，然后Kncod开通Lighthouse的防火墙访问策略，允许客户端访问服务器的业务端口。支持多实例，支持TCP和UDP，关键参数可配置。

# 需求场景

## 背景
- 服务端：61.170.71.133，腾讯云轻量应用服务器，但不希望所有人都可以连接它，只对受信任的客户端IP开放特定端口。
- 客户端：83.94.156.180，一个或者多个，经常变换IP

## 需求

客户端向服务端指定端口敲门（请求一个特定的URL），服务端通过腾讯云API，在防火墙上创建规则，允许客户端IP访问其他业务端口。

<img width="60%" alt="image" border="1" src="https://github.com/uf1y/TencentCloud-Lighthouse-IP-Knockdoor/assets/117698857/9df33c47-a05b-42b9-a6d0-176259c4abde">

# Knockd服务端安装使用

## 网络要求

- 轻量应用服务器的防火墙开放`0.0.0.0/0`对`TCP/80`端口的访问
- 轻量应用服务器主机防火墙处于关闭状态

## 组件要求

`Python 3.0`是基本要求，在此基础上安装如下模块：

```
pip install requests
pip install tornado
pip install dot_env
pip install tencentcloud-sdk-python
```

## 安装运行
```bash
git clone --depth=1 https://github.com/uf1y/TencentCloud-Lighthouse-IP-Knockdoor.git
cd TencentCloud-Lighthouse-IP-Knockdoor
mv .env.sample .env
# Windows: move .env.sample .env
# 使用前请先修改配置文件: vi .env
python knockd_start.py
```

# 功能阐述
## 服务端主逻辑
- Knockd服务监听在`TCP/8080`端口；
- Lighthouse防火墙默认开放`0.0.0.0/0`对`TCP/8080`的访问
- 客户端敲门请求：`http://<KNOCKD_SERVER>:8080/favico.ico`，URL可以自定义
- 服务端识别出客户端IP地址和目标服务的端口（通过配置文件自定义），将IP地址添加到腾讯云轻量应用服务器的防火墙

## 客户端使用

### HTTP请求格式

```HTML
GET /favico.ico HTTP/1.1
Host: <KNOCKD_SERVER_IP>:8080
User-Agent: curl/8.1.2
Accept: */*
Referer:https://www.baidu..com/
Location:Offfice_01
```

### Curl请求方式：
```bash
curl  -H "Referer:https://www.baidu..com/" \
      -H "Location:Offfice_01" \
      http://<KNOCKD_SERVER_IP>/favico.ico
```

### 其它

你也可以通过其它程序或自动化手段实现敲门请求，例如iOS快捷指令，只要符合HTTP请求格式即可。

## 防火墙配置结果

<img width="80%" alt="image" border="1" src="https://github.com/uf1y/TencentCloud-Lighthouse-IP-Knockdoor/assets/117698857/29c6afef-0303-4849-8b74-123944b33930">

# 关键说明

## 服务端HTTP返回的错误信息

为了防止返回数据被中间设备监听或用于特征分析，所有客户端到服务端请求的返回结果都是`HTTP 500`，唯一的区别是返回的内容：
- 成功：`500 Internal Server Error.`
- 失败：`500 Internal Server Error`

> 返回字符串可以在`.env`文件中配置

## 安全组规满了怎么办？

每一次敲门成功后，系统都会执行一次规则清理逻辑。`默认会删除30天以前由本敲门程序创建的其他规则。`

> 如果你的客户端长期没有活跃，也没有执行过敲门程序，那么有可能被Knockd服务从防火墙规则中移除。

## 配置文件.env

配置文件`.env`默认放在程序主目录下，也可以在系统环境变量的其他目录，主要配置说明如下：

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

## 客户端如何做到出口IP变更之后自动敲门？

好问题，建议参考：[do-something-when-your-internet-ip-changed](https://github.com/uf1y/do-something-when-your-internet-ip-changed)。
