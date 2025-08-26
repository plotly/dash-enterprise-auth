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
from retrying import retry as _retry

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


@_retry(wait_exponential_multiplier=1000, wait_exponential_max=20000)
def _get_public_keys(jwks_client):
    return jwks_client.get_signing_keys()


jwks_url = _os.getenv("DASH_JWKS_URL", "")
jwks_client = UaPyJWKClient(jwks_url)
public_keys = None
if jwks_url:
    public_keys = _get_public_keys(jwks_client)


def _get_public_key(token):
    kid = _jwt.get_unverified_header(token)["kid"]
    for key in public_keys:
        if key._jwk_data["kid"] == kid:
            return key.key


def _get_de5_user_data(jwt_id_token):
    public_key = _get_public_key(jwt_id_token)
    decoded_token = _jwt.decode(jwt_id_token, public_key, algorithms=["RS256"], audience="dash")
    return decoded_token


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

    if not _os.getenv("DASH_JWKS_URL") and hasattr(_dcc, "LogoutButton"):
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


def is_jupyter_kernel():
    """Check if the current environment is a Jupyter kernel."""
    try:
        return get_ipython().__class__.__name__ == "ZMQInteractiveShell"  # type: ignore
    except NameError:
        return False


def _raise_context_error():
    notebook_specific_error = (
        (
            "Could not get user token from the Jupyter kernel. Try closing and re-opening your notebook. \n"
            "This codeblock will still run correctly in your App Studio preview or deployed Dash app."
        )
        if _os.getenv("DASH_ENTERPRISE_ENV")
        else (
            "Could not get user token from the Jupyter kernel.\n"
            "dash-enterprise-auth methods cannot be called in a notebook cell outside of a Dash Enterprise workspace.\n"
            "This codeblock will still run correctly in your App Studio preview or deployed Dash app."
        )
    )
    raise RuntimeError(
        notebook_specific_error
        if is_jupyter_kernel()
        else "Could not find user token from the context.\n"
        "Make sure you are running inside a flask request or a dash callback."
    )


def _get_decoded_token(name):
    token = _undefined
    if _flask.has_request_context():
        token = _flask.request.cookies.get(name)
    if token is _undefined and hasattr(_dash.callback_context, "cookies"):
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

        # In workspace, the user token is stored via the dash_user_token environment
        # variable to make it available in the Jupyter kernel.
        dash_user_token = is_jupyter_kernel() and _os.getenv("DASH_USER_TOKEN")

        token = dash_user_token or _get_decoded_token("kcIdToken")

        if not token:
            return {}

        signing_key = jwks_client.get_signing_key_from_jwt(token)

        info = _jwt.decode(
            token,
            signing_key.key,
            algorithms=[signing_key._jwk_data.get("alg", "RSA256")],
            # This is fine because the token is already present in the client's cookies
            # in the workspace.
            audience="account"
            if is_jupyter_kernel()
            else _os.getenv("DASH_AUD", "dash"),
            options={"verify_exp": True},
        )
        if info_url:
            tok = dash_user_token or _get_decoded_token("kcToken")
            authorization = f"Bearer {dash_user_token or tok.decode()}"
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
    if not _os.getenv("DASH_JWKS_URL"):
        data = get_user_data()
        return data.get("username")
    token = _get_decoded_token("kcIdToken")
    data = _get_de5_user_data(token)
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
