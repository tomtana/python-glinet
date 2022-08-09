import time

import requests
import crypt
import hashlib
import getpass
import exceptions
import decorators
import re
import logging
import threading
import warnings
import utils
import api_helper


class GlInet:

    def __init__(self,
                 url="https://192.168.8.1/rpc",
                 username="root",
                 password=None,
                 protocol_version="2.0",
                 keep_alive=True,
                 keep_alive_intervall=30,
                 verify_ssl_certificate=False,
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
            return utils.ResultContainer(typename, json_data)
        else:
            return utils.ResultContainer(f"{method}", json_data)

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

    @decorators.login_required
    def is_alive(self):
        if self.sid is None:
            return False
        try:
            resp = self.request("alive", {"sid": self.sid})
        except exceptions.AccessDeniedError:
            return False
        return True

    @decorators.login_required
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
        logging.info(f"Loading api description from {self._api_reference_url}")
        resp = requests.get(self._api_reference_url)
        api = resp.json()["data"]
        api = {utils.sanitize_string(i["module_name"][0]): i for i in api}
        return api

    @decorators.login_required
    def get_api_client(self):
        return api_helper.GlInetApi(self._api_desciption, self)


if __name__ == "__main__":
    glinet = GlInet()
    glinet.login()
    api_client = glinet.get_api_client()
