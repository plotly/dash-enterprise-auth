"""
dash-enterprise-auth

Methods to integrate dash apps with the authentication from Dash Enterprise.
"""

import datetime as _dt
import os as _os
import platform as _platform
import base64 as _b64
import functools as _ft
import json as _json
import urllib as _urllib
from typing import Any

import flask as _flask
import jwt as _jwt
import requests as _requests
import traceback


import dash as _dash

if hasattr(_dash, "dcc"):
    _dcc = _dash.dcc
else:
    import dash_core_components as _dcc
if hasattr(_dash, "html"):
    _html = _dash.html
else:
    import dash_html_components as _html

from .version import __version__

ua_string = (
    f"Plotly/{__version__} (Language=Python/{_platform.python_version()};"
    f" Platform={_platform.system()}/{_platform.release()})"
)

_undefined = object()

class UaPyJWKClient(_jwt.PyJWKClient):
    def fetch_data(self) -> Any:
        with _urllib.request.urlopen(
            _urllib.request.Request(self.uri, headers={"User-Agent": ua_string})
        ) as response:
            return _json.load(response)


def _need_request_context(func):
    @_ft.wraps(func)
    def _wrap(*args, **kwargs):
        if not _flask.has_request_context():
            raise RuntimeError(
                f"`{func.__name__}` method needs a flask/dash request"
                f" context to run. Make sure to run `{func.__name__}` from a callback."
            )
        return func(*args, **kwargs)

    return _wrap


def create_logout_button(label="Logout", style=None):
    """
    Create a dcc.LogoutButton with the Dash Enterprise logout url set
    in the environment.

    :param label: Text of the logout button.
    :type label: str
    :param style: Extra style to add to the logout button.
    :type style: dict
    :return:
    """
    logout_url = _os.getenv("DASH_LOGOUT_URL")
    if not logout_url:
        raise RuntimeError("DASH_LOGOUT_URL was not set in the environment.")

    if not _os.getenv("DASH_JWKS_URL"):
        return _dcc.LogoutButton(
            logout_url=logout_url,
            label=label,
            style=style,
        )

    btn_style = {"display": "inline-block"}
    if style:
        btn_style.update(style)

    return _html.Div(
        _html.A(
            label,
            href=logout_url,
            className="dash-logout-btn",
            style={"textDecoration": "none"},
        ),
        className="dash-logout-frame",
        style=btn_style,
    )


def _raise_context_error():
    try:
        is_jupyter_kernel = (
            get_ipython().__class__.__name__ == "ZMQInteractiveShell"  # type: ignore
        )
    except NameError:
        is_jupyter_kernel = False

    raise RuntimeError(
        "dash-enterprise-auth functions should be called in a flask request context or dash callback and will not run in a notebook cell.\n"
        "This codeblock will still run correctly in your App Studio preview or deployed Dash app."
        if is_jupyter_kernel
        else "Could not find user token from the context.\n"
        "Make sure you are running inside a flask request or a dash callback."
    )


def _get_decoded_token(name):
    token = _undefined
    if _flask.has_request_context():
        token = _flask.request.cookies.get(name)
    if not token and hasattr(_dash.callback_context, "cookies"):
        token = _dash.callback_context.cookies.get(name)
    if token is _undefined:
        _raise_context_error()
    if token is None:
        return token
    return _b64.b64decode(token)


def get_user_data():
    jwks_url = _os.getenv("DASH_JWKS_URL")
    info_url = _os.getenv("DASH_USER_INFO_URL")
    if not jwks_url:
        if not _flask.has_request_context():
            # Old DE4 should always be in a request context.
            _raise_context_error()
        return _json.loads(_flask.request.headers.get("Plotly-User-Data", "{}"))
    try:
        jwks_client = UaPyJWKClient(jwks_url)

        token = _get_decoded_token("kcIdToken")

        if not token:
            return {}

        signing_key = jwks_client.get_signing_key_from_jwt(token)

        info = _jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key._jwk_data.get("alg", "RSA256")],
            audience=_os.getenv("DASH_AUD", "dash"),
            options={"verify_exp": True},
        )
        if info_url:
            tok = _get_decoded_token("kcToken")
            authorization = f"Bearer {tok.decode()}"
            response = _requests.get(
                info_url,
                headers={
                    "User-Agent": ua_string,
                    "Authorization": authorization,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            info.update(data)

        return info
    except Exception as e:
        print("JWT decode error: " + repr(e))
        traceback.print_exc()
    return {}


def get_username():
    """
    Get the current user.

    :return: The current user.
    :rtype: str
    """
    data = get_user_data()
    if not _os.getenv("DASH_JWKS_URL"):
        return data.get("username")
    return data.get("preferred_username")


@_need_request_context
def get_kerberos_ticket_cache():
    """
    Get the kerberos ticket for the current logged user.

    :return: The kerberos ticket cache.
    """
    data = get_user_data()

    expiry_str = data["kerberos_ticket_expiry"]
    expiry = _dt.datetime.strptime(expiry_str, "%Y-%m-%dT%H:%M:%SZ")
    if expiry < _dt.datetime.utcnow():
        raise Exception("Kerberos ticket has expired.")

    return _b64.b64decode(data["kerberos_ticket_cache"])
