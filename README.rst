|GitHub Workflow Status (event)| |GitHub Pages| |PyPI - Python Version| |PyPI| |Code Cov|


python-glinet - A Python3 Client for GL.Inet Router
===================================================

-  **Python3 client providing full access to the GL.Inet Luci API.**
-  **Supported firmware versions: 4.0 onwards**
-  **Dynamic method creation including docstring from the gl.inet online
   documentation**
-  **Api responses are recursively build as objects, such that you
   can access all properties via '.'**
-  **Cache for api description and hashed login**
-  **Configurable background thread to keep connection alive**

.. image:: https://github.com/tomtana/python-glinet/raw/main/ressources/python_glinet_demo.gif

.. note::

   -  GL.Inet changed the api mechanism from REST to JSON-RPC with the introduction of the firmware 4.0. Therefore, older versions are not supported.
   -  There is no official documentation in English yet. The client parses the Chinese documentation from `here <https://dev.gl-inet.cn/docs/api_docs_page>`__ and dynamically creates the api methods. Once it is available, the repo will be updated.
   -  The best way to navigate and explore the api is within an ipython shell. A wrapper for ipython and terminal is on the roadmap.

Installation
-------------

PIP
~~~

.. code-block:: sh

   pip install python-glinet

From Repo
~~~~~~~~~

.. code-block:: sh

   #clone repository
   git clone https://github.com/tomtana/python-glinet.git
   cd python-glinet

It is strongly recommended to install the package inside an python
virtual environment (see `here <https://docs.python.org/3/tutorial/venv.html>`__ for more infos). The pip
parameter ``-e`` is optional, and gives you the possibility to edit the ``python-glinet`` module in the cloned folder.

.. code-block:: sh

   python3 -m venv venv
   source venv/bin/activate
   pip install -e .

Getting Started
---------------

The heart piece of  ``python-glinet`` is the ``GlInet`` class. It is manages authentication, session and communication
with the api. In case you modified the router default settings such as ip-address or username you need to pass them as
parameter (see the documentation of the `GlInet <https://tomtana.github.io/python-glinet/glinet.html>`__ class for more details).

For browsing the api using the dynamically created api_client, it is assumed that the commands are executed in an
ipython shell.



.. warning::

    Even though possible, it is strongly discouraged to pass the password as a parameter.

.. note::

   -  The constructor is checking if a api description is already in the cache and will load it from the gl.inet online documentation if not.
   -  Make sure you check and understand the default settings

.. code:: python

   from pyglinet import GlInet
   glinet = GlInet()

..

Login
~~~~~

.. code:: python

   glinet.login()

..

.. note::

   -  if no password is passed as parameter in the constructor, ``login()`` will try to load login data from persistence
   -  if no success ask via prompt and persist settings
   -  start background thread to keep connection alive

API Access Via Dynamically Created Client
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure you are in an ipython shell and logged in. Then, generate the ``api_client``.

.. code:: python

   client = glinet.get_api_client()

General
^^^^^^^

-  The api structure is as follow:
   **client.<functionial_group>.<method>**
-  Due to python naming rules for variables, all "-" are replaced with
   "_" for the api method construction. **e.g. wg-client becomes
   wg_client.**
-  Use code completion and docstring to intuitively navigate the api

Functional Groups
^^^^^^^^^^^^^^^^^

Just call your client to see all available api function groups.

::

   client

.. collapse:: Output

    .. code:: bash

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



Methods
^^^^^^^

To explore the methods of a function group, just select it and hit
enter.

.. code:: python

   client.wg_client

.. collapse:: Output

    .. code:: bash

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

Parameters
^^^^^^^^^^

Select your method and press enter. A list for all possible parameters
are printed. If a parameter is prepended with ``?``, it means it is
optional.

.. code:: python

   api.wg_client.set_config

.. collapse:: Output

    .. code:: bash

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

Docstring
^^^^^^^^^

You can also show the docstring by appending a ``?`` to the method. It
will show all the parameter and usage examples.

.. code:: text

   api.wg_client.set_config?

.. collapse:: Output

    .. code:: text

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

Method call
^^^^^^^^^^^

Just call the method as usual. Check the usage examples to understand
how parameters need to be passed.

::

   client.wg_client.get_all_config_list()

.. code:: bash

   Out[12]: {'name': 'wg_client__get_all_config_list', 'config_list': [{'name': 'wg_client__get_all_config_list', 'username': '', 'group_name': 'AzireVPN', 'peers': [], 'password': '', 'auth_type': 1, 'group_id': 9690}]}

API Response Processing
^^^^^^^^^^^^^^^^^^^^^^^

The API json responses are recursively converted into objects. This
provides convenient access with code completion and point access to the
data.

API Access Via Direct Request
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of using the dynamically created api_client, it is also possible
to use the ``GlInet`` instance to make api requests. In fact, the
api_client uses the ``GlInet`` session under the hood.

Once logged in, you simply can use the
``glinet.request(method, params)`` method to access or retrieve data
from the api. Information about the method and the parameters can either
be found in the
`documentation <https://dev.gl-inet.cn/docs/api_docs_page>`__ or via the
api_client.

e.g.

::

   glinet.request("call", ["adguardhome", "get_config"])

.. code:: bash

   Out[12]: {'name': 'adguardhome__get_config', 'id': 13, 'jsonrpc': '2.0', 'result': {'name': 'adguardhome__get_config', 'enabled': False}}

is equivalent to

::

   api_client.adguardhome.get_config()

.. code:: bash

   Out[13]: {'name': 'adguardhome__get_config', 'enabled': False}

..

.. note::

   The output of the ``request`` method returns the whole
   response body whereas the api_client just returns the result dict.


Roadmap
-------


V1.0.0
~~~~~~

-  ☒ Add dynamically docstring for API calls
-  ☒ Create pip compliant package
-  ☒ Publish pip package
-  ☒ Add tests
-  ☒ Improve documentation
-  ☒ Increase test coverage
-  ☐ replace crypt dependency to allow also Windows execution
-  ☐ Add wrapper for execution via terminal


V2.0.0
~~~~~~
-  ☐ Add asyncio support
-  ☐ ...

.. |GitHub Workflow Status (event)| image:: https://img.shields.io/github/workflow/status/tomtana/python-glinet/Python%20package
   :target: https://github.com/tomtana/python-glinet/actions/workflows/python-package.yml
.. |PyPI - Python Version| image:: https://img.shields.io/pypi/pyversions/python-glinet
   :target: https://pypi.org/project/python-glinet
.. |PyPI| image:: https://img.shields.io/pypi/v/python-glinet
   :target: https://pypi.org/project/python-glinet
.. |image3| image:: /ressources/python_glinet_demo.gif
.. |GitHub Pages| image:: https://img.shields.io/github/workflow/status/tomtana/python-glinet/Deploy%20static%20content%20to%20Pages?label=docs
   :alt: GitHub Workflow Status
   :target: https://tomtana.github.io/python-glinet/
.. |Code Cov| image:: https://codecov.io/gh/tomtana/python-glinet/branch/main/graph/badge.svg?token=976L8ESH8K
 :target: https://codecov.io/gh/tomtana/python-glinet