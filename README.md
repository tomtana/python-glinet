# python-glinet - A Python3 Client for GL.Inet Router
**This python client provides full access to the GL.Inet Luci API.**

**Supported firmware versions: 4.0 onwards**

## About:
My original use case was to automatically generate and write nordvpn wireguard configs to my slate axt-1800 router but then
found an elegant way to autogenerate calls for the whole api and it got out of hand :).

It should be noted that GL.Inet changed the api mechanism from REST to JSON-RPC with the introduction of the firmware 4.0. Therefore, older
versions are not supported.

Also, there is no official documentation in English yet. The client parses the Chinese documentation from [here](https://dev.gl-inet.cn/docs/api_docs_page)  and dynamically 
creates the api methods. Once it is available, the repo will be updated. 

The best way to navigate through the api is within an ipython shell. A wrapper for ipython and terminal is on the roadmap, but for now you must
start ipython first and then load the module. 

Of course, you can also build your own application around, just bear in mind that
the api function calls are generated on the fly and therefore not available when writing your program. 



## Features
- Complete API support
- Dynamic method creation inclusive docstring from online documentation
- Api responses are represented recursively as objects, such that you can access all properties via '.'
- Cache for api description and hashed login
- Configure background thread to keep connection alive

![](/ressources/python_glinet_demo.gif)

## Installation:

### PiP
```
pip install python-glinet
```

### From Repo
```
#clone repository
git clone https://github.com/tomtana/python-glinet.git
cd python-glinet
```

Install package directly. The `-e` parameter lets you edit the files. 
If this is not needed to can also install without the `-e` parameter.
```
pip install -e .
```

Alternatively install it in an Python virtual environment (see [here](https://docs.python.org/3/tutorial/venv.html) 
for more infos)
```
python3 -m venv venv
source venv/bin/activate
pip install -e .
```
## Getting Started

### Login
Login is as easy as that. If you modified your ip-address or other parameter, 
you need to pass them as parameter (see the documentation of the GlInet class for more details).

Per default the following steps are executed:
- if no password is passed
  - try to load from persistance (password stored as hash)
  - if no success ask via prompt
- try to load api reference from persistence, otherwise load it from the web
- persist settings
- start background thread to keep connection alive

Start ipython shell and make sure you sourced your venv if you use one.
```python
from pyglinet import GlInet
glinet = GlInet()
glinet.login()
```

### API Usage
First generate an api object.
```python
client = glinet.get_api_client()
```

#### General

- The api structure is as follow: **client.\<functionial_group\>.\<method\>**
- Due to python naming rules for variables, all "-" are replaced with "_" for the api method construction. **e.g. wg-client becomes wg_client.**
- Use code completion and docstring to intuitively navigate the api

#### Functional Groups
Just call your client to see all available api function groups.
```
client

Out[11]: 
Function
------------------
repeater
rs485
qos
acl
modem
logread
igmp
custom_dns
dns
dlna
nas_web
adguardhome
s2s
samba
switch_button
diag
rtty
network
upgrade
reboot
wg_server
firewall
ovpn_server
vpn_policy
fan
system
wg_client
cable
led
ui
netmode
ddns
ipv6
ovpn_client
plugins
tethering
macclone
lan
edgerouter
clients
wifi
cloud
cloud_batch_manage
```
#### Methods
To explore the methods of a function group, just select it and hit enter.
```python
client.wg_client

Out[6]:
Function
--------------------
get_recommend_config
get_third_config
add_config
set_config
remove_config
clear_config_list
get_config_list
start
stop
get_status
check_config
confirm_config
add_group
remove_group
set_group
get_group_list
get_all_config_list
set_proxy
add_route
set_route
get_route_list
remove_route
```
#### Parameters
Select your method and press enter. A list for all possible parameters are printed. If a parameter is prepended with `?`, it means it is optional.

```python
api.wg_client.set_config

Out[8]: 
Parameter              Type    Description
---------------------  ------  ------------------
name                   string  节点名
address_v4             string  节点IPv4子网
?address_v6            string  节点IPv6子网
private_key            string  节点私钥
allowed_ips            string  节点的allowedips
end_point              string  节点的endpoint
public_key             string  节点公钥
?dns                   string  节点的dns
?preshared_key         string  预分享密钥
?ipv6_enable           bool    是否启用IPv6
presharedkey_enable    bool    是否使用预分享密钥
group_id               number  组ID
peer_id                number  配置ID
?listen_port           number  监听端口
?persistent_keepalive  number  节点保活
?mtu                   number  节点的mtu
```
#### Docstring
You can also show the docstring by appending a `?` to the method. It will show all the parameter and usage examples.
```python
api.wg_client.set_config?

Signature: api.wg_client.set_config(params=None)
Type:      GlInetApiCall
File:      ~/.local/lib/python3.10/site-packages/pyglinet/api_helper.py
Docstring:
Available parameters (?=optional):
Parameter              Type    Description
---------------------  ------  ------------------
name                   string  节点名
address_v4             string  节点IPv4子网
?address_v6            string  节点IPv6子网
private_key            string  节点私钥
allowed_ips            string  节点的allowedips
end_point              string  节点的endpoint
public_key             string  节点公钥
?dns                   string  节点的dns
?preshared_key         string  预分享密钥
?ipv6_enable           bool    是否启用IPv6
presharedkey_enable    bool    是否使用预分享密钥
group_id               number  组ID
peer_id                number  配置ID
?listen_port           number  监听端口
?persistent_keepalive  number  节点保活
?mtu                   number  节点的mtu

Example request:
{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":[\"\",\"wg-client\",\"set_config\",{\"group_id\":3212,\"peer_id\":1254,\"name\":\"test\",\"address_v4\":\"10.8.0.0/24\",\"address_v6\":\"fd00:db8:0:123::/64\",\"private_key\":\"XVpIdr+oYjTcgDwzSZmNa1nSsk8JO+tx1NBo17LDBAI=\",\"allowed_ips\":\"0.0.0.0/0,::/0\",\"end_point\":\"103.231.88.18:3102\",\"public_key\":\"zv0p34WZN7p2vIgehwe33QF27ExjChrPUisk481JHU0=\",\"dns\":\"193.138.219.228\",\"presharedkey_enable\":false,\"listen_port\":22536,\"persistent_keepalive\":25,\"mtu\":1420,\"ipv6_enable\":true}],\"id\":1}

Example response:
{\"jsonrpc\": \"2.0\", \"id\": 1, \"result\": {}}
```

#### Method call
Just call the method as usual. Check the usage examples to understand how parameters need to be passed.

```
client.wg_client.get_all_config_list()

Out[12]: {'name': 'wg_client__get_all_config_list', 'config_list': [{'name': 'wg_client__get_all_config_list', 'username': '', 'group_name': 'AzireVPN', 'peers': [], 'password': '', 'auth_type': 1, 'group_id': 9690}]}
```

#### API Response Processing
The API json responses are recursively converted into objects. This provides convenient access with code completion and point access to the data.

## ToDos:
- [x] Add dynamically docstring for API calls
- [x] Create pip compliant package
- [x] Publish pip package
- [ ] Add tests
- [ ] Improve documentation
- [ ] Add wrapper for execution via terminal
