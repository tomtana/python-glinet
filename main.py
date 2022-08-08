import time

import requests
import crypt
import hashlib
import os
import getpass
import exceptions
from decorators import login_required
from collections import namedtuple, OrderedDict
import re
import asyncio
import logging
import threading
import warnings
import utils


class GlInetBase:

    def __init__(self, url="https://192.168.8.1/rpc", username="root", password=None,
                 protocol_version="2.0", keep_alive=True, keep_alive_intervall=30, verify_ssl_certificate=False,
                 api_reference_url="https://dev.gl-inet.cn/docs/api_docs_api/"):
        self.url = url
        self.query_id = 0
        if password is None:
            self.password = getpass.getpass(prompt='Enter your GL-Inet password')
        else:
            self.password = password
        self.username = username
        self.protocol_version = protocol_version
        self.session = requests.session()
        self.sid = None
        self._keep_alive = keep_alive
        self._keep_alive_intervall = keep_alive_intervall
        self._thread = None
        self._lock = threading.Lock()
        self._verify_ssl_certificate = verify_ssl_certificate
        if self._verify_ssl_certificate is False:
            logging.warning("You disabled ssl certificate validation. Further warning messages will be deactivated.")
            warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        self._api_reference_url = api_reference_url
        self._api_desciption = self.__load_api_desciption()

    def __generate_query_id(self):
        qid = self.query_id
        self.query_id = (self.query_id + 1) % 9999999999
        return qid

    def __generate_request(self, method, params):
        # if there was an successful login before
        if self.sid:
            if isinstance(params, dict):
                params_ = {"sid": self.sid}
                params_.update(params)
                return {
                    "jsonrpc": self.protocol_version,
                    "id": self.__generate_query_id(),
                    "method": method,
                    "params": params_
                }
            else:
                return {
                    "jsonrpc": self.protocol_version,
                    "id": self.__generate_query_id(),
                    "method": method,
                    "params": [self.sid] + list(params)
                }
        else:
            return {
                "jsonrpc": self.protocol_version,
                "id": self.__generate_query_id(),
                "method": method,
                "params": params
            }

    def request(self, method, params):
        req = self.__generate_request(method, params)
        self._lock.acquire()
        resp = self.session.post(self.url, json=req, verify=False)
        self._lock.release()
        if resp.json().get("error", None):
            error_ = resp.json().get("error")
            if error_["code"] == -32000:
                raise exceptions.AccessDeniedError(f"Access denied, error output: {error_}")
            else:
                raise ConnectionError(resp.json())
        if resp.status_code != 200:
            raise ConnectionError(f"Status code {resp.status_code} returned. Response content: \n\n {resp.content}")
        if resp.json().get("result", None) and resp.json().get("result", None).get("err_msg", None):
            raise ConnectionError(resp.json())
        return self.__create_object(resp.json(), method, params)

    def __create_object(self, json_data, method, params):

        if method == "call":
            typename = f"{params[0]}__{params[1]}"
            typename = re.sub(r"[,\-!/]", "_", typename)
            return utils.create_recursive_object(json_data, typename)
        else:
            return utils.create_recursive_object(json_data, f"{method}")

    def __challenge_login(self):
        resp = self.request("challenge", {"username": self.username})
        return resp.result

    def login(self):
        challenge = self.__challenge_login()
        hash = self.__generate_hash(challenge)
        resp = self.request("login", {"username": self.username,
                                      "hash": hash})
        self.sid = resp.result.sid

        # start keep alive thread
        if self._keep_alive:
            self._thread = threading.Thread(target=self.__keep_alive)
            self._thread.start()
        return True

    def __keep_alive(self):
        logging.info(f"Starting keep alive thread at intvervall {self._keep_alive_intervall}")
        while self._keep_alive:
            logging.debug(f"keep alive with intervall {self._keep_alive_intervall}")
            if not self.is_alive():
                logging.warning("client disconnected, trying to login again..")
                self.login()
            time.sleep(self._keep_alive_intervall)
        logging.info("Keep alive halted.")

    @login_required
    def is_alive(self):
        if self.sid is None:
            return False
        try:
            resp = self.request("alive", {"sid": self.sid})
        except exceptions.AccessDeniedError:
            return False
        return True

    @login_required
    def logout(self):
        self.request("logout", {"sid": self.sid})
        self.sid = None
        return True

    def __generate_openssl_passwd(self, alg, salt):
        return crypt.crypt(self.password, f"${alg}${salt}")

    def __generate_hash(self, challenge):
        openssl_pwd = self.__generate_openssl_passwd(challenge.alg, challenge.salt)
        hash = hashlib.md5(f'{self.username}:{openssl_pwd}:{challenge.nonce}'.encode()).hexdigest()
        return hash

    def __load_api_desciption(self):
        resp = requests.get(self._api_reference_url)
        api = resp.json()["data"]
        api = {utils.sanitize_string(i["module_name"][0]): i for i in api}
        return api

    def get_api_client(self):
        pass


class GlInetApiObject:
    def __init__(self, data, session):
        self._session = session
        for name, value in data.items():
            setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return GlInetApi(value, self._session) if isinstance(value, dict) else value

    def call(self):
        self.__call__()

    def __call__(self, params=None):
        p = []
        if params:
            p = list(params)
        p = self.module_name + [self.data.title] + p
        return self._session.request("call", p)


class GlInetApi:
    def __init__(self, data, session):
        self._session = session
        if data.get("case_groups_data", None):
            for name, value in data.get("case_groups_data").items():
                setattr(self, name, GlInetApiObject(value, self._session))
        else:
            for name, value in data.items():
                setattr(self, name, self._wrap(value))

    def _wrap(self, value):
        if isinstance(value, (tuple, list, set, frozenset)):
            return type(value)([self._wrap(v) for v in value])
        else:
            return GlInetApi(value, self._session) if isinstance(value, dict) else value


"""    
ApiObject ->

wg-client, led, ovpn, etc..

wg-client.description
wg-client.get_bla_bli_blubb(parameter1, parameter2) 
 """

if __name__ == "__main__":
    client = GlInetBase()
    client.login()
    # r = client.request("call", ["ovpn-server", "get_config", {}])
