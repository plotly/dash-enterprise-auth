import base64

import pytest
import flask
import jwt
import time
from jwt import PyJWK

from dash import html, dcc

secret_key = "abovetopsecret"

key_data = {
    "kty": "oct",
    "alg": "HS256",
    "k": base64.urlsafe_b64encode(secret_key.encode())
}

AUD = "dash-aud"
LOGOUT_URL = 'https://logout.e.com'

def create_mock_getter(env):
    def get(key, default=None):
        return env.get(key, default)

    return get


@pytest.mark.parametrize("environ, headers, cookies", [
    ({}, {"Plotly-User-Data": '{"username": "Mario"}'}, {}),
    (
            {"DASH_JWKS_URL": "Hello World", "DASH_AUD": AUD},
            {},
            {"kcIdToken": base64.b64encode(jwt.encode(
                {"preferred_username": "Mario", "exp": time.time() + 60, "aud": AUD},
                secret_key, algorithm="HS256",
            ).encode())}
    )
])
def test_get_username(mocker, environ, headers, cookies):
    mocker.patch("os.getenv", create_mock_getter(environ))
    mocker.patch(
        "dash_enterprise_auth.UaPyJWKClient.get_signing_key_from_jwt",
        return_value=PyJWK(key_data)
    )
    with flask.Flask(__name__).test_request_context():
        mocker.patch("flask.has_request_context", return_value=True)
        mocker.patch("flask.request.headers.get", create_mock_getter(headers))
        mocker.patch("flask.request.cookies.get", create_mock_getter(cookies))

        import dash_enterprise_auth as dea

        username = dea.get_username()

        assert username == "Mario"


@pytest.mark.parametrize("environ, type_assertions", [
    ({
        'DASH_LOGOUT_URL': LOGOUT_URL,
    }, [([], dcc.LogoutButton, {'label': 'Logout', 'logout_url': LOGOUT_URL})]),
    ({
        'DASH_LOGOUT_URL': LOGOUT_URL,
        'DASH_JWKS_URL': 'https://foo.bar'
    }, [
        ([], html.Div, {'style': {'display': 'inline-block', 'padding': '1rem'}}),
        (['children'], html.A, {'children': 'Logout', 'href': LOGOUT_URL})
    ])
])
def test_create_logout_button(mocker, environ, type_assertions):
    mocker.patch("os.getenv", create_mock_getter(environ))

    import dash_enterprise_auth as dea

    logout_button = dea.create_logout_button(style={'padding': '1rem'})

    for path, tas, props in type_assertions:
        current = logout_button

        for p in path:
            current = getattr(current, p)

        assert isinstance(current, tas)

        for k, v in props.items():
            assert getattr(current, k) == v
