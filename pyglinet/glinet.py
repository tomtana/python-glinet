import time
import os
import requests
from passlib.hash import md5_crypt as md5
from passlib.hash import sha256_crypt as sha256
from passlib.hash import sha512_crypt as sha512
import getpass
import hashlib
import pyglinet.exceptions as exceptions
import pyglinet.decorators as decorators
import re
import logging
import threading
import warnings
from pyglinet import utils
import pyglinet.glinet_api as api_helper
import pathlib
import pickle
from typing import Union, List, Dict
import shutil

log = logging.getLogger(__name__)


class GlInet:
    """
    This class manages the connection to a GL-Inet router and provides basic routines to send and receive data.

    Important: Only works with firmware version >=4.0. The api has changed from REST api to json-rpc with the 4.0,
    so older firmware versions won't work.

    Before you can start making requests, you need to call the :meth:`~pyglinet.GlInet.login` method

    The api calls can either be made via the GlInetApi object,
    which can be constructed via the get_api_client method, or via the request method directly.
    """

    _algo_map = {
        "1": lambda passwd, salt: md5.hash(passwd, salt=salt),
        "5": lambda passwd, salt: sha256.hash(passwd, salt=salt, rounds=5000),
        "6": lambda passwd, salt: sha512.hash(passwd, salt=salt, rounds=5000)
    }

    def __init__(self,
                 url: str = "https://192.168.8.1/rpc",
                 username: str = "root",
                 password: Union[str, None] = None,
                 protocol_version: str = "2.0",
                 keep_alive: bool = True,
                 keep_alive_intervall: float = 30,
                 verify_ssl_certificate: bool = False,
                 update_api_reference_cache: bool = False,
                 api_reference_url: str = "https://dev.gl-inet.cn/docs/api_docs_api/",
                 cache_folder: str = None):
        """
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
        :param cache_folder: folder where data is persisted. If left empty, default is `$home/.python-pyglinet`
        """
        self._url = url
        self._query_id = 0
        if cache_folder is None:
            self._cache_folder = pathlib.Path.home()
            self._cache_folder = os.path.join(self._cache_folder, ".python-glinet")
            log.info(f"Creating folder {self._cache_folder} if not exist")
            pathlib.Path(self._cache_folder).mkdir(exist_ok=True)
        else:
            if os.path.exists(cache_folder):
                self._cache_folder = cache_folder
            else:
                raise FileExistsError(f"Path {cache_folder} doesnt exist.")
        self._password = password
        self._username = username
        self._protocol_version = protocol_version
        self._session = requests.session()
        self._sid = None
        self._keep_alive = keep_alive
        self._keep_alive_intervall = keep_alive_intervall
        self._thread = None
        self._lock = threading.Lock()
        self._verify_ssl_certificate = verify_ssl_certificate
        if self._verify_ssl_certificate is False:
            log.warning("You disabled ssl certificate validation. Further warning messages will be deactivated.")
            warnings.filterwarnings('ignore', message='Unverified HTTPS request')
        self._cached_login_data = None
        self._login_cache_path = os.path.join(self._cache_folder, "login.pkl")
        self._api_reference_cache_path = os.path.join(self._cache_folder, "api_reference.pkl")
        self._api_reference_url = api_reference_url
        self._api_description = self.__load_api_description(update_api_reference_cache)
        self._api = None
        self._keep_alive_interrupt_event = threading.Event()

    def __del__(self):
        self._stop_keep_alive_thread()

    def __generate_query_id(self) -> int:
        """
        Generate json-rpc query id

        :return: query id
        """
        qid = self._query_id
        self._query_id = (self._query_id + 1) % 9999999999
        return qid

    def __generate_request(self, method: str, params: Union[Dict, List[str], str]) -> dict:
        """
        Generate json for rpc api call

        :param method: rpc method
        :param params: params

        :return: json
        """
        # if there was an successful login before
        if self._sid:
            if isinstance(params, dict):
                params_ = {"sid": self._sid}
                params_.update(params)
                return {
                    "jsonrpc": self._protocol_version,
                    "id": self.__generate_query_id(),
                    "method": method,
                    "params": params_
                }
            else:
                return {
                    "jsonrpc": self._protocol_version,
                    "id": self.__generate_query_id(),
                    "method": method,
                    "params": [self._sid] + list(params)
                }
        else:
            return {
                "jsonrpc": self._protocol_version,
                "id": self.__generate_query_id(),
                "method": method,
                "params": params
            }

    def __request(self, method: str, params: Union[Dict, List[str], str]) -> utils.ResultContainer:
        """
        Send request to router without considering the current login state. This may lead to misleading error messages.

        :param method: rpc method
        :param params: parameter

        :return: ResultContainer
        """
        req = self.__generate_request(method, params)
        self._lock.acquire()
        resp = self._session.post(self._url, json=req, verify=False)
        self._lock.release()
        if resp.status_code != 200:
            raise ConnectionError(f"Status code {resp.status_code} returned. Response content: \n\n {resp.content}")
        if resp.json().get("error", None):
            error_ = resp.json().get("error")
            if error_["code"] == -32000:
                raise exceptions.AccessDeniedError(f"Access denied, error output: {error_}")
            elif error_["code"] == -32602:
                raise exceptions.WrongParametersError(f"Wrong params in request, error output: {error_}")
            elif error_["code"] == -32601:
                raise exceptions.MethodNotFoundError(
                    f"Wrong method {req.get('method', None)} in request, error output: {error_}")
            else:
                raise ConnectionError(resp.json())
        if resp.json().get("result", None) and resp.json().get("result", None).get("err_msg", None):
            raise ConnectionError(resp.json())
        return self.__create_object(resp.json(), method, params)

    @decorators.login_required
    def __request_with_sid(self, method: str, params: Union[Dict, List[str], str]) -> utils.ResultContainer:
        """
        Request which requires prior login

        :param method: api method call
        :param params: params

        :return: ResultContainer
        """
        return self.__request(method, params)

    @decorators.logout_required
    def __request_without_sid(self, method: str, params: Union[Dict, List[str], str]) -> utils.ResultContainer:
        """
        Request which requires to be logged out

        :param method: api method call
        :param params: params

        :return: ResultContainer
        """
        return self.__request(method, params)

    def request(self, method: str, params: Union[Dict, List[str], str]) -> utils.ResultContainer:
        """
        Send request. Function checks if method requires login and chooses the respective request wrapper.
        see :meth:`~pyglinet.GlInet.__request_with_sid` and :meth:`~pyglinet.GlInet.__request`

        :param method: api method call
        :param params: params

        :return: ResultContainer
        """
        if method in ["challenge", "alive"]:
            return self.__request(method, params)
        elif method in ["login"]:
            return self.__request_without_sid(method, params)
        else:
            return self.__request_with_sid(method, params)

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
        Request cryptographic parameters to compute login hash. This is the first step in the login
        sequence.

        :return: challence
        """
        resp = self.request("challenge", {"username": self._username})
        return resp.result

    def login(self) -> "GlInet":
        """
        Login and start background thread for keep_alive is configured. If password was set in constructor,
        cached values will be ignored. If password was not set (default) in :meth:`~pyglinet.GlInet`, you will be asked to enter the password
        the first time this function is called. If login was successful, the password hash is cashed.

        :return: GlInet
        """

        if self.is_alive():
            log.info("Already logged in, nothing to do.")
            return self

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
            resp = self.request("login", {"username": self._username,
                                          "hash": login_hash})
            self._sid = resp.result.sid
        except exceptions.AccessDeniedError:
            log.warning("Could not login with current credentials, deleting cached credentials.")
            self._cached_login_data = None
            self._sid = None
            os.remove(self._login_cache_path)
            raise

        # start keep alive thread
        if self._keep_alive:
            self._start_keep_alive_thread()
        return self

    @decorators.login_required
    def _start_keep_alive_thread(self):
        """
        Starts keep alive background thread which calls :meth:`~pyglinet.GlInet.__keep_alive`
        in the configured interval.

        :return:
        """
        if self._thread is None or not self._thread.is_alive():
            log.debug("Starting background keep alive thread.")
            self._keep_alive_interrupt_event.clear()
            self._thread = threading.Thread(target=self.__keep_alive)
            self._thread.start()
        else:
            raise exceptions.KeepAliveThreadActiveError("Keep alive thread is already alive.")

    def _stop_keep_alive_thread(self):
        """
        Stop keep alive thread
        """
        if hasattr(self, "_thread") and self._thread and self._thread.is_alive():
            log.info(f"Shutting down background thread. This will take max {self._keep_alive_intervall} seconds.")
            self._keep_alive_interrupt_event.set()
            self._thread.join()

    def __update_login_and_cache(self, challenge, update_password=False):
        """
        Generates the login struct containing username, hash, salt and alg type. If data is diverging from
        persisted set, old data will be deleted and new data will be persisted to file.

        :param challenge: challenge as received containing nonce, salt and algo
        :param update_password: if True, the user will be requested to enter the password
        """
        password = self._password

        if update_password:
            password = getpass.getpass(prompt='Enter your GL-Inet password')

        _hash = self.__generate_unix_passwd_hash(password, challenge.alg, challenge.salt)
        login_data = {"username": self._username,
                      "hash": _hash,
                      "salt": challenge.salt,
                      "alg": challenge.alg}
        if login_data != self._cached_login_data:
            self._cached_login_data = login_data
            self.__dump_to_file(self._cached_login_data, self._login_cache_path)

    def __load_if_exist(self, file: str):
        """
        Load pickle file if it exists.

        :param file: path to file

        :return: None if file doesn't exist, else Data
        """
        loaded_data = None
        if os.path.exists(file):
            with open(file, "rb") as f:
                try:
                    loaded_data = pickle.load(f)
                except:
                    log.warning(f"Something went wrong loading file {file}")
        return loaded_data

    def __dump_to_file(self, obj, file):
        """
        Dump pickle data to file.

        :param obj: object to dump
        :param file: path to file

        :return: None
        """
        if not pathlib.Path(file).parent.exists():
            pathlib.Path(file).parent.mkdir(exist_ok=True)

        with open(file, "wb") as f:
            pickle.dump(obj, f)

    def __keep_alive(self) -> None:
        """
        Keep connection alive

        Function is started in background thread (see login() for more details). Send in fixed intervall requests to api.
        If not successful, try to connect again.

        :return: None
        """
        log.info(f"Starting keep alive thread at intvervall {self._keep_alive_intervall}")
        while self._keep_alive and not self._keep_alive_interrupt_event.is_set():
            log.debug(f"keep alive with intervall {self._keep_alive_intervall}")
            if not self.is_alive():
                log.warning("client disconnected, trying to login again..")
                self.login()
            self._keep_alive_interrupt_event.wait(self._keep_alive_intervall)
        log.info("Keep alive halted.")

    def flush_cache(self) -> None:
        """
        Deletes the folder containing persisted login and api description as well as cached login data.
        It will NOT invalidate or reload api data. To achieve that see :meth:`~pyglinet.GlInet.get_api_client`

        :return: None
        """
        if os.path.exists(self._cache_folder):
            shutil.rmtree(self._cache_folder)
        self._cached_login_data = None
        log.info(f"Login cache cleared and folder {self._cache_folder} deleted")

    def is_alive(self) -> bool:
        """
        Check if connection is alive.

        :return: True if alive, else False
        """
        if self._sid is None:
            return False
        try:
            resp = self.request("alive", {"sid": self._sid})
        except exceptions.AccessDeniedError:
            return False
        return True

    def logout(self) -> bool:
        """
        Logout and stop keep alive thread

        :return: True
        """
        if self.is_alive():
            self.request("logout", {"sid": self._sid})
        self._session.cookies.clear()
        self._sid = None
        self._stop_keep_alive_thread()
        return True

    def __generate_unix_passwd_hash(self, password: str, alg: str, salt: str) -> str:
        """
        Generate unix style hash with given algo and salt

        :param alg: algorithm
        :param salt: salt

        :return: hash
        """
        hash_func = self._algo_map.get(f"{alg}", None)
        if not hash_func:
            raise exceptions.UnsupportedHashAlgoError(f"The algo {alg} is not supported. Supported Algos: {self._algo_map}")
        return hash_func(password, salt=salt)

    def __generate_login_hash(self, challenge):
        """
        Generate final authentication hash

        :param challenge: dict with nonce, salt and algo type

        :return: authentication hash
        """
        return hashlib.md5(f'{self._username}:{self._cached_login_data["hash"]}:{challenge.nonce}'.encode()).hexdigest()

    def __load_api_description(self, update: bool = False):
        """
        Load api description in json format

        :param update: if true, the api description is loaded from the web. If false, the program first tries to load
            the data from the cache and in case this fails from the web.

        :return: api description
        """
        api_description = None
        if update or not os.path.exists(self._api_reference_cache_path):
            log.info(f"Loading api description from {self._api_reference_url}")
            resp = requests.get(self._api_reference_url)
            api_description = resp.json()["data"]
            api_description = {utils.sanitize_string(i["module_name"][0]): i for i in api_description}
            pathlib.Path(self._cache_folder).mkdir(exist_ok=True)
            with open(self._api_reference_cache_path, "wb") as f:
                log.info(f"Updating cache file {self._api_reference_cache_path}")
                pickle.dump(api_description, f)
        else:
            with open(self._api_reference_cache_path, "rb") as f:
                api_description = pickle.load(f)

        return api_description

    @decorators.login_required
    def get_api_client(self, update_description=False) -> api_helper.GlInetApi:
        """
        Create GlInetApi object client to access api functions

        :param update_description: if True, api description is updated from web
        :return: GlInetApi
        """
        if not self._api_description or update_description:
            self._api_description = self.__load_api_description(True)
            self._api = api_helper.GlInetApi(self._api_description, self)
        if not self._api:
            self._api = api_helper.GlInetApi(self._api_description, self)

        return self._api

    @property
    def api(self) -> api_helper.GlInetApi:
        """
        Method gives access to the autogenerated api functions. See also :meth:`~pyglinet.GlInet.get_api_client`

        :return: GlInetApi
        """
        return self.get_api_client()
