"""
dash-enterprise auth

Methods to integrate dash apps with the authentication from the
dash-deployment-server.
"""
from .version import __version__
import datetime as _dt
import os as _os
import base64 as _b64
import functools as _ft
import json as _json

import dash as _dash
if hasattr(_dash, "dcc"):
    _dcc = _dash.dcc
else:
    import dash_core_components as _dcc
import flask as _flask


logout_url = _os.getenv('DASH_LOGOUT_URL')


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
    return _json.loads(_flask.request.headers.get('Plotly-User-Data', "{}"))


@_need_request_context
def get_username():
    """
    Get the current user.

    :return: The current user.
    :rtype: str
    """
    return get_user_data().get('username')


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
