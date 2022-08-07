import requests
import crypt
import hashlib
import os
import getpass
import exceptions
from decorators import login_required
from collections import namedtuple, OrderedDict
import re

url = "https://192.168.8.1/"
query_id = 0


class GlInet:

    def __init__(self, url="https://192.168.8.1/rpc", username="root", password=None,
                 protocol_version="2.0"):
        self.url = url
        self.query_id = 0
        if password is None:
            self.password = getpass.getpass(prompt='Enter your AXT-1800 password')
        else:
            self.password = password
        self.username = username
        self.protocol_version = protocol_version
        self.session = requests.session()
        self.sid = None

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
        resp = self.session.post(self.url, json=req, verify=False)
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

        def create_recursive_object(obj, obj_name):
            if isinstance(obj, dict):
                fields = sorted(obj.keys())
                namedtuple_type = namedtuple(
                    typename=obj_name,
                    field_names=fields,
                    rename=True,
                )
                field_value_pairs = OrderedDict(
                    (str(field), create_recursive_object(obj[field], obj_name)) for field in fields)
                try:
                    return namedtuple_type(**field_value_pairs)
                except TypeError:
                    # Cannot create namedtuple instance so fallback to dict (invalid attribute names)
                    return dict(**field_value_pairs)
            elif isinstance(obj, (list, set, tuple, frozenset)):
                return [create_recursive_object(item, obj_name) for item in obj]
            else:
                return obj

        if method == "call":
            typename = f"{params[0]}__{params[1]}"
            typename = re.sub(r"[,\-!/]", "_", typename)
            return create_recursive_object(json_data, typename)
        else:
            return create_recursive_object(json_data, f"{method}")

    def __challenge_login(self):
        resp = self.request("challenge", {"username": self.username})
        return resp.result

    def login(self):
        challenge = self.__challenge_login()
        hash = self.__generate_hash(challenge)
        resp = self.request("login", {"username": self.username,
                                      "hash": hash})
        self.sid = resp.result.sid
        return True

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


client = GlInet()
client.login()
#r = client.request("call", ["ovpn-server", "get_config", {}])
