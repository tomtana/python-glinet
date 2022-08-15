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


@pytest.fixture
def glinet_base():
    return GlInet(password=r"jdlkjLJlkd=(//&%/&dskdBBDs192837")


@pytest.mark.vcr()
def test_successful_login_logout(glinet_base):
    assert glinet_base.login(), "Login was not successful"
    with pytest.raises(exceptions.LoggedInError) as e:
        glinet_base.login()
    assert glinet_base._thread.is_alive(), "Keep alive thread not working"
    glinet_base._stop_keep_alive_thread()
    glinet_base._thread.join()
    assert not glinet_base._thread.is_alive(), "Keep alive thread still running"
    assert glinet_base.logout(), "Logout was not successful"
    with pytest.raises(exceptions.NotLoggedInError) as e:
        glinet_base.logout()
    assert os.path.exists(glinet_base._login_cache_path), "Login cache file was not created."

@pytest.mark.vcr()
def test_unsuccessful_login():
    glinet_base = GlInet(password="wrong_password")
    with pytest.raises(exceptions.AccessDeniedError) as e:
        glinet_base.login()
    assert not os.path.exists(
        glinet_base._login_cache_path), "Login cache file was not deleted after entering wrong credentials."
    assert glinet_base._thread is None, "Keep alive thread running"
