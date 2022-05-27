"""
dash-enterprise auth

Methods to integrate dash apps with the authentication from the
dash-deployment-server.
"""
from .version import __version__
import datetime as _dt
import os as _os
import platform as _platform
import base64 as _b64
import functools as _ft
import json as _json
import jwt as _jwt
import urllib as _urllib
from typing import Any

import dash as _dash
if hasattr(_dash, "dcc"):
    _dcc = _dash.dcc
else:
    import dash_core_components as _dcc
import flask as _flask

logout_url = _os.getenv('DASH_LOGOUT_URL')
ua_string = 'Plotly/%s (Language=Python/%s; Platform=%s/%s)' % (__version__, _platform.python_version(), _platform.system(), _platform.release())


class UaPyJWKClient(_jwt.PyJWKClient):
    def fetch_data(self) -> Any:
        with _urllib.request.urlopen(_urllib.request.Request(self.uri, headers={'User-Agent': ua_string})) as response:
            return _json.load(response)


def _need_request_context(func):
    @_ft.wraps(func)
    def _wrap(*args, **kwargs):
        if not _flask.has_request_context():
            raise RuntimeError('`{0}` method needs a flask/dash request'
                               ' context to run. Make sure to run '
                               '`{0}` from a callback.'.format(func.__name__))
        return func(*args, **kwargs)
    return _wrap


def create_logout_button(label='Logout'):
    """
    Create a dcc.LogoutButton with the dash-deployment-server logout url set
    in the environment.

    :param label: Text of the logout button.
    :type label: str
    :return:
    """
    if not logout_url:
        raise Exception(
            'DASH_LOGOUT_URL was not set in the environment.'
        )

    return _dcc.LogoutButton(
        logout_url=logout_url,
        label=label,
    )


@_need_request_context
def get_user_data():
    jwks_url = _os.getenv('DASH_JWKS_URL')
    if not jwks_url:
        return _json.loads(_flask.request.headers.get('Plotly-User-Data', "{}"))
    try:
        jwks_client = UaPyJWKClient(jwks_url)

        b64token = _flask.request.cookies.get('kcIdToken')
        token = _b64.b64decode(b64token)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        return _jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key._jwk_data.get('alg', 'RSA256')],
            audience=_os.getenv('DASH_AUD', "dekn-dev"),
            options={"verify_exp": True},
        )
    except Exception as e:
        print("JWT decode error: " + repr(e))
    return {}


@_need_request_context
def get_username():
    """
    Get the current user.

    :return: The current user.
    :rtype: str
    """
    data = get_user_data()
    if not _os.getenv('DASH_JWKS_URL'):
        return data.get('username')
    return data.get('preferred_username')


@_need_request_context
def get_kerberos_ticket_cache():
    """
    Get the kerberos ticket for the current logged user.

    :return: The kerberos ticket cache.
    """
    data = get_user_data()

    expiry_str = data['kerberos_ticket_expiry']
    expiry = _dt.datetime.strptime(expiry_str, '%Y-%m-%dT%H:%M:%SZ')
    if expiry < _dt.datetime.utcnow():
        raise Exception('Kerberos ticket has expired.')

    return _b64.b64decode(data['kerberos_ticket_cache'])
