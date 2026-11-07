"""Client for dw's /api/selfhosted API, authenticated by the mapserver key.

A failure here must never stop the server working locally, so callers get a
result or a False back, and nothing raises.
"""
import requests

import config


TIMEOUT = 10


def _request(method, path, **kwargs):
    return requests.request(
        method,
        "{0}/selfhosted{1}".format(config.api_url().rstrip("/"), path),
        headers={"Authorization": "Bearer " + config.ollebo_key()},
        timeout=TIMEOUT,
        **kwargs
    )


def check_connection():
    """Return (connected, detail), where detail is for showing to the user."""
    if not config.ollebo_key():
        return False, "No map key configured"
    try:
        resp = _request("GET", "/self")
    except requests.RequestException as e:
        return False, "Can't reach ollebo.com: {0}".format(e.__class__.__name__)
    if resp.status_code == 401:
        return False, "Map key not accepted"
    if resp.status_code != 200:
        return False, "HTTP {0}".format(resp.status_code)
    try:
        body = resp.json()
        return True, "{0} in {1}".format(body["mapserver"]["name"], body["space"]["slug"])
    except (ValueError, KeyError, TypeError):
        return False, "Unexpected response from ollebo.com"


def _send(method, path, what, **kwargs):
    if not config.ollebo_key():
        return False
    try:
        resp = _request(method, path, **kwargs)
    except requests.RequestException as e:
        print("ollebo: {0} failed: {1}".format(what, e.__class__.__name__))
        return False
    if not resp.ok:
        print("ollebo: {0} failed: HTTP {1}".format(what, resp.status_code))
    return resp.ok


def save_public_url():
    return _send(
        "PATCH",
        "/self",
        "saving public URL",
        json={"url": config.terracotta_public_url()},
    )


def register_map(map_id, payload):
    return _send(
        "PUT",
        "/maps/{0}".format(requests.utils.quote(map_id, safe="")),
        "registering {0}".format(map_id),
        json=payload,
    )
