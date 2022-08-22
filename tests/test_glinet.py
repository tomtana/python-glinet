import time
import pytest
from pyglinet import GlInet, exceptions
import os
import sys
from io import StringIO
from contextlib import contextmanager


@contextmanager
def replace_stdin(target):
    orig = sys.stdin
    sys.stdin = target
    yield
    sys.stdin = orig


@pytest.fixture(scope="module")
def glinet_base():
    gl = GlInet(password=r"jdlkjLJlkd=(//&%/&dskdBBDs192837")
    yield gl
    gl.logout()


@pytest.mark.vcr()
def test_login_logout_caching(glinet_base):
    time.sleep(0.3)
    assert glinet_base.login(), "Login was not successful"

    assert glinet_base._thread.is_alive(), "Keep alive thread not working"
    glinet_base._stop_keep_alive_thread()
    glinet_base._thread.join()

    assert not glinet_base._thread.is_alive(), "Keep alive thread still running"

    assert glinet_base.logout(), "Logout was not successful"
    assert not glinet_base.is_alive(), "client is still alive"
    assert os.path.exists(glinet_base._login_cache_path), "Login cache file was not created."
    assert os.path.exists(glinet_base._api_reference_cache_path), "Api cache file was not created."


@pytest.mark.vcr()
def test_keep_alive(glinet_base):
    time.sleep(0.3)
    assert glinet_base.login(), "Login was not successful"
    assert glinet_base.is_alive(), "Not logged in"
    assert glinet_base._thread.is_alive(), "Keep alive thread not working"
    glinet_base.logout()
    glinet_base._thread.join()
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
    glinet_base._thread.join()
    assert not glinet_base.is_alive(), "Still logged in"
    assert not glinet_base._thread.is_alive(), "Keep alive thread still running"


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
def test_api_client_01(glinet_base):
    time.sleep(0.3)
    glinet_base.login()
    api_client = glinet_base.get_api_client()
    # check if request and api client have same behaviour
    res1 = api_client.clients.get_status()
    res2 = glinet_base.request("call", ["clients", "get_status"]).result
    assert res1 == res2, "Diverging result with same api method."

    # read and write
    api_client.led.set_config([{"led_enable": False}])
    assert not api_client.led.get_config().led_enable, "Value has not been set"
    api_client.led.set_config([{"led_enable": True}])
    assert api_client.led.get_config().led_enable, "Value has not been set"


@pytest.mark.vcr()
def test_requests(glinet_base):
    time.sleep(0.3)
    glinet_base.login()
    with(pytest.raises(exceptions.LoggedInError)):
        glinet_base.request("login", {})
    glinet_base.logout()
    with(pytest.raises(exceptions.NotLoggedInError)):
        glinet_base.request("logout", {})
        glinet_base.request("call", ["whatever", "is_here"])
