import time
import os
import requests
import crypt
import hashlib
import getpass
import pyglinet.exceptions as exceptions
import pyglinet.decorators as decorators
import re
import logging
import threading
import warnings
from pyglinet import utils
import pyglinet.api_helper as api_helper
import pathlib
import pickle


class GlInet:

    def __init__(self,
                 url="https://192.168.8.1/rpc",
                 username="root",
                 password=None,
                 protocol_version="2.0",
                 keep_alive=True,
                 keep_alive_intervall=30,
                 verify_ssl_certificate=False,
                 update_api_reference_cache=False,
                 api_reference_url="https://dev.gl-inet.cn/docs/api_docs_api/",
                 cache_folder=None):
        """
        This class manages the connection to a GL-Inet router and provides basic routines to send and receive data.

        Important: Only works with firmware version >=4.0. The api has changed from REST api to json-rpc with the 4.0,
        so older firmware versions won't work.


        The specific api calls are coordinated via the GlInetApi object,
        which can be constructed via the get_api_client method.

        :param url: url to router rpc api
        :param username: username, default is root.
        :param password: password, if left empty, a prompt will ask you when login() is called. For security reasons,
        you should never pass your password here.
        :param protocol_version: default 2.0
        :param keep_alive: if set to True, a background thread will be started to keep the connection alive
        :param keep_alive_intervall: intervall in which the background thread sends requests to the router
        :param verify_ssl_certificate: either True/False or path to certificate.
        :param update_api_reference_cache: if True, data is loaded from the web, otherwise application tries first to
        load data from cache.
        :param api_reference_url: url to api description
        :param cache_folder: folder where data is persisted. If left empty, default is $home/.python-pyglinet
        """
        self.url = url
        self.query_id = 0
        if cache_folder is None:
            self._cache_folder = pathlib.Path.home()
            self._cache_folder = os.path.join(self._cache_folder, ".python-pyglinet")
            logging.info(f"Creating folder {self._cache_folder} if not exist")
            pathlib.Path(self._cache_folder).mkdir(exist_ok=True)
        else:
            if os.path.exists(cache_folder):
                self._cache_folder = cache_folder
            else:
                raise FileNotFoundError(f"Path {cache_folder} doesnt exist.")
        self._password = password
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
        self._cached_login_data = None
        self._login_cache_path = os.path.join(self._cache_folder, "login.pkl")
        self._api_reference_cache_path = os.path.join(self._cache_folder, "api_reference.pkl")
        self._api_reference_url = api_reference_url
        self._api_desciption = self.__load_api_desciption(update_api_reference_cache)
        self._keep_alive_interrupt_event = threading.Event()

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

    @decorators.logout_required
    def login(self):
        """
        Login

        Login and start background thread for keep_alive is configured. If password was set,
        cached values will be ignored.
        :return: True
        """
        challenge = self.__challenge_login()
        if self._password is None:
            self._cached_login_data = self.__load_if_exist(self._login_cache_path)
            if not self._cached_login_data:
                self.__update_login_and_cache(challenge, update_password=True)
        else:
            self.__update_login_and_cache(challenge, update_password=False)

        try:
            # call challenge again since otherwise it will timeout
            challenge = self.__challenge_login()
            login_hash = self.__generate_login_hash(challenge)
            resp = self.request("login", {"username": self.username,
                                          "hash": login_hash})
            self.sid = resp.result.sid
        except exceptions.AccessDeniedError:
            logging.warning("Could not login with current credentials, deleting cached credentials.")
            self._cached_login_data = None
            os.remove(self._login_cache_path)
            raise

        # start keep alive thread
        if self._keep_alive:
            self._start_keep_alive_thread()
        return True

    @decorators.login_required
    def _start_keep_alive_thread(self):
        if self._thread is None or not self._thread.is_alive():
            logging.debug("Starting background keep alive thread.")
            self._keep_alive_interrupt_event.clear()
            self._thread = threading.Thread(target=self.__keep_alive)
            self._thread.start()

    def _stop_keep_alive_thread(self):
        logging.info(f"Shutting down background thread. This will take max {self._keep_alive_intervall} seconds.")
        self._keep_alive_interrupt_event.set()

    def __update_login_and_cache(self, challenge, update_password=False):
        password = self._password

        if update_password:
            password = getpass.getpass(prompt='Enter your GL-Inet password')

        _hash = self.__generate_unix_passwd_hash(password, challenge.alg, challenge.salt)
        login_data = {"username": self.username,
                      "hash": _hash,
                      "salt": challenge.salt,
                      "alg": challenge.alg}
        if login_data != self._cached_login_data:
            self._cached_login_data = login_data
            self.__dump_to_file(self._cached_login_data, self._login_cache_path)

    def __load_if_exist(self, file):
        """
        Load pickle file if it exists.
        :param file: path to file
        :return: None if file doesnt exist, else Data
        """
        loaded_data = None
        if os.path.exists(file):
            with open(file, "rb") as f:
                try:
                    loaded_data = pickle.load(f)
                except:
                    logging.warning(f"Something went wrong loading file {file}")
        return loaded_data

    def __dump_to_file(self, obj, file):
        """
        Dump pickle data to file.
        :param file: path to file
        :return: None
        """
        with open(file, "wb") as f:
            pickle.dump(obj, f)

    def __keep_alive(self):
        """
        Keep connection alive

        Function is started in background thread (see login() for more details). Send in fixed intervall requests to api.
        If not successful, try to connect again.
        :return: None
        """
        logging.info(f"Starting keep alive thread at intvervall {self._keep_alive_intervall}")
        while self._keep_alive and not self._keep_alive_interrupt_event.is_set():
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
        Logout and stop keep alive thread
        :return: True
        """
        self.request("logout", {"sid": self.sid})
        self.sid = None
        self._stop_keep_alive_thread()
        return True

    def __generate_unix_passwd_hash(self, password, alg, salt):
        """
        Generate unix style hash with given algo and salt
        :param alg: algorithm
        :param salt: salt
        :return: hash
        """
        return crypt.crypt(password, f"${alg}${salt}")

    def __generate_login_hash(self, challenge):
        """
        Generate final authentication hash
        :param challenge: dict with nonce, salt and algo type
        :return: authentication hash
        """
        return hashlib.md5(f'{self.username}:{self._cached_login_data["hash"]}:{challenge.nonce}'.encode()).hexdigest()

    def __load_api_desciption(self, update=False):
        """
        Load api description in json format

        @:param update: if true, the api description is loaded from the web. If false, the program first tries to load
        the data from the cache and in case this fails from the web.
        :return: api description
        """
        api_description = None
        if update or not os.path.exists(self._api_reference_cache_path):
            logging.info(f"Loading api description from {self._api_reference_url}")
            resp = requests.get(self._api_reference_url)
            api_description = resp.json()["data"]
            api_description = {utils.sanitize_string(i["module_name"][0]): i for i in api_description}
            with open(self._api_reference_cache_path, "wb") as f:
                logging.info(f"Updating cache file {self._api_reference_cache_path}")
                pickle.dump(api_description, f)
        else:
            with open(self._api_reference_cache_path, "rb") as f:
                api_description = pickle.load(f)

        return api_description

    def check_initialized(self):
        self.request("call", "")

    @decorators.login_required
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
