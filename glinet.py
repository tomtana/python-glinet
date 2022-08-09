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
        """
        This class manages the connection to a GL-Inet router and provides basic routines to send and receive data.

        Important: Only works with firmware version >=4.0. The api has changed from REST api to json-rpc with the 4.0,
        so older firmware versions won't work.


        The specific api calls are coordinated via the GlInetApi object,
        which can be constructed via the get_api_client method.

        :param url: url to router rpc api
        :param username: username, default is root.
        :param password: password, if left empty, a prompt will ask you when login() is called
        :param protocol_version: default 2.0
        :param keep_alive: if set to True, a background thread will be started to keep the connection alive
        :param keep_alive_intervall: intervall in which the background thread sends requests to the router
        :param verify_ssl_certificate: either True/False or path to certificate.
        :param api_reference_url: url to api description
        """
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
        """
        Generate json-rpc query id
        :return: query id
        """
        qid = self.query_id
        self.query_id = (self.query_id + 1) % 9999999999
        return qid

    def __generate_request(self, method, params):
        """
        Generate json for rpc api call
        :param method: rpc method
        :param params: params
        :return: json
        """
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
        """
        Send request to router
        :param method: rpc method
        :param params: parameter
        :return: result
        """
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
        """
        Create recursive object from json api response

        Json data is stored in a convenience container, such that elements can be accessed as class attributes via '.'
        :param json_data: json data
        :param method: api method call
        :param params: params
        :return: ResultContainer
        """
        if method == "call":
            typename = f"{params[0]}__{params[1]}"
            typename = re.sub(r"[,\-!/]", "_", typename)
            return utils.ResultContainer(typename, json_data)
        else:
            return utils.ResultContainer(f"{method}", json_data)

    def __challenge_login(self):
        """
        Login challenge

        Requests required information to start login process.
        :return: challence
        """
        resp = self.request("challenge", {"username": self.username})
        return resp.result

    def login(self):
        """
        Login

        Login and start background thread for keep_alive is configured.
        :return: True
        """
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
        """
        Keep connection alive

        Function is started in background thread (see login() for more details). Send in fixed intervall requests to api.
        If not successful, try to connect again.
        :return: None
        """
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
        """
        Check if connection is alive.
        :return: True if alive, else False
        """
        if self.sid is None:
            return False
        try:
            resp = self.request("alive", {"sid": self.sid})
        except exceptions.AccessDeniedError:
            return False
        return True

    @decorators.login_required
    def logout(self):
        """
        Logout
        :return: True
        """
        self.request("logout", {"sid": self.sid})
        self.sid = None
        return True

    def __generate_openssl_passwd(self, alg, salt):
        """
        Generate unix style hash with given algo and salt
        :param alg: algorithm
        :param salt: salt
        :return: hash
        """
        return crypt.crypt(self.password, f"${alg}${salt}")

    def __generate_hash(self, challenge):
        """
        Generate final authentication hash
        :param challenge: dict with nonce, salt and algo type
        :return: authentication hash
        """
        openssl_pwd = self.__generate_openssl_passwd(challenge.alg, challenge.salt)
        hash = hashlib.md5(f'{self.username}:{openssl_pwd}:{challenge.nonce}'.encode()).hexdigest()
        return hash

    def __load_api_desciption(self):
        """
        Load api descipton in json format from docu page
        :return: api description
        """
        logging.info(f"Loading api description from {self._api_reference_url}")
        resp = requests.get(self._api_reference_url)
        api = resp.json()["data"]
        api = {utils.sanitize_string(i["module_name"][0]): i for i in api}
        return api

    def get_api_client(self):
        """
        Create client to access api functions
        :return: api client
        """
        return api_helper.GlInetApi(self._api_desciption, self)


if __name__ == "__main__":
    glinet = GlInet()
    glinet.login()
    api_client = glinet.get_api_client()
