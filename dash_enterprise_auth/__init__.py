"""
dash-enterprise auth

Methods to integrate dash apps with the authentication from the
dash-deployment-server.
"""
import datetime as _dt
import os as _os
import base64 as _b64
import functools as _ft

import dash_core_components as _dcc
import flask as _flask

from . import _api_requests


__version__ = '0.0.1'

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
def get_username():
    """
    Get the current user.

    :return: The current user.
    :rtype: str
    """
    user_data = _flask.request.headers.get('Plotly-User-Data', {})
    return user_data.get('username')


@_need_request_context
def get_kerberos_ticket_cache():
    """
    Get the kerberos ticket for the current logged user.

    :return: The kerberos ticket cache.
    """
    token = _flask.request.cookies.get('plotly_oauth_token')

    res = _api_requests.get(
        '/v2/users/current?kerberos=1',
        headers={'Authorization': 'Bearer {}'.format(token)},
    )
    res_json = res.json()

    expiry_str = res_json['kerberos_ticket_expiry']
    expiry = _dt.datetime.strptime(expiry_str, '%Y-%m-%dT%H:%M:%SZ')
    if expiry < _dt.datetime.utcnow():
        raise Exception('Kerberos ticket has expired.')

    return _b64.b64decode(res_json['kerberos_ticket_cache'])
