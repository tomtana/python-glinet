import time
import pytest
from pyglinet import GlInet, exceptions
import os
import sys
from io import StringIO
from contextlib import contextmanager
import pathlib


@contextmanager
def replace_stdin(target):
    orig = sys.stdin
    sys.stdin = target
    yield
    sys.stdin = orig


@pytest.fixture(scope="module")
def glinet_base():
    gl = GlInet(password=r"jdlkjLJlkd=(//&%/&dskdBBDs192837", keep_alive=False)
    yield gl
    gl._stop_keep_alive_thread()


@pytest.fixture(autouse=True)
def glinet(glinet_base):
    glinet_base.login()
    time.sleep(0.3)
    return glinet_base


@pytest.mark.vcr()
def test_login_logout_caching(glinet_base):
    time.sleep(0.3)
    assert glinet_base.login(), "Login was not successful"
    time.sleep(0.3)

    assert glinet_base.logout(), "Logout was not successful"
    assert not glinet_base.is_alive(), "client is still alive"
    assert os.path.exists(glinet_base._login_cache_path), "Login cache file was not created."
    assert os.path.exists(glinet_base._api_reference_cache_path), "Api cache file was not created."

    # check if data is loaded from cache
    gl = GlInet()

    # check if custom path is working
    cache_folder = pathlib.Path.home().as_posix() + "/.python-glinet"
    pathlib.Path(cache_folder).mkdir(exist_ok=True)
    gl = GlInet(cache_folder=cache_folder)
    with pytest.raises(FileExistsError):
        gl = GlInet(cache_folder="/doesnt_exist")
    with replace_stdin(StringIO("jdlkjLJlkd=(//&%/&dskdBBDs192837")) as s:
        gl = GlInet(keep_alive=False)
        os.remove(gl._login_cache_path)
        time.sleep(0.3)
        gl.login()
        gl.logout()
        # load now login from cache
        time.sleep(0.3)
        gl.login()
        gl.logout()


@pytest.mark.vcr()
def test_keep_alive(glinet_base):
    time.sleep(0.3)
    glinet_base._keep_alive = True
    assert glinet_base.login(), "Login was not successful"
    glinet_base._start_keep_alive_thread()
    assert glinet_base.is_alive(), "Not logged in"
    assert glinet_base._thread.is_alive(), "Keep alive thread not working"
    with pytest.raises(exceptions.KeepAliveThreadActiveError):
        glinet_base._start_keep_alive_thread()
    glinet_base._sid = glinet_base._sid[:-2] + "aA"
    assert not glinet_base.is_alive(), "Should not be alive but is"
    glinet_base.logout()
    assert not glinet_base.is_alive(), "Still logged in"
    assert not glinet_base._thread.is_alive(), "Keep alive thread still running"
    time.sleep(0.3)
    glinet_base.login()
    assert glinet_base._thread.is_alive(), "Keep alive thread not working"
    with pytest.raises(exceptions.MethodNotFoundError) as e:
        glinet_base.request("call", ["non_existent", "parameter"])
    assert glinet_base._thread.is_alive(), "Keep alive thread not working"
    assert glinet_base.is_alive(), "Not logged in"
    glinet_base.logout()
    assert not glinet_base.is_alive(), "Still logged in"
    assert not glinet_base._thread.is_alive(), "Keep alive thread still running"
    glinet_base._keep_alive = False


@pytest.mark.vcr()
def test_unsuccessful_login():
    glinet_test = GlInet(password="wrong_password")
    with pytest.raises(exceptions.AccessDeniedError) as e:
        glinet_test.login()
    assert not os.path.exists(
        glinet_test._login_cache_path), "Login cache file was not deleted after entering wrong credentials."
    assert glinet_test._thread is None, "Keep alive thread running"
    with pytest.raises(exceptions.NotLoggedInError) as e:
        glinet_test.get_api_client()
    with pytest.raises(exceptions.NotLoggedInError) as e:
        glinet_test.request("call", ["led", "get-config"])


@pytest.mark.vcr()
def test_api_client_01(glinet):
    time.sleep(0.3)
    glinet.login()
    api_client = glinet.get_api_client()
    # check if request and api client have same behaviour
    res1 = api_client.clients.get_status()
    res2 = glinet.request("call", ["clients", "get_status"]).result
    res3 = api_client.clients.get_status.call()
    assert res1 == res2 == res3, "Diverging result with same api method."

    #test str and repr from ResultContainer
    str(res1)
    repr(res1)

    # read and write
    api_client.led.set_config([{"led_enable": False}])
    assert not api_client.led.get_config().led_enable, "Value has not been set"
    api_client.led.set_config.call([{"led_enable": True}])
    assert api_client.led.get_config().led_enable, "Value has not been set"
    str(api_client.clients.get_status)
    repr(api_client.clients.get_status)
    str(api_client.clients)
    repr(api_client.clients)
    str(api_client)
    repr(api_client)


@pytest.mark.vcr()
def test_requests(glinet):
    time.sleep(0.3)
    glinet.login()
    api_client = glinet.get_api_client()
    with(pytest.raises(exceptions.LoggedInError)):
        glinet.request("login", {})
    with pytest.raises(exceptions.WrongParametersError):
        glinet.request("call", ["wrong_parameter"])
    with pytest.raises(exceptions.MethodNotFoundError):
        glinet.request("call", ["led", "wrong_method"])
    glinet.logout()
    with(pytest.raises(exceptions.NotLoggedInError)):
        glinet.request("logout", {})
    with(pytest.raises(exceptions.NotLoggedInError)):
        glinet.request("call", ["whatever", "is_here"])
    with(pytest.raises(exceptions.NotLoggedInError)):
        api_client.led.get_config()


@pytest.mark.vcr()
def test_no_api_description(glinet):
    api_description = glinet._api_description
    glinet._api_description = None
    with(pytest.raises(exceptions.NoApiDescriptionError)):
        glinet.get_api_client()
    glinet._api_description = api_description
