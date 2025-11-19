import json

import requests
from requests.auth import HTTPDigestAuth
from requests.sessions import Session

from janus.logging import logger


def make_digest_request(
    method, url, username, apikey, verify_ssl=True, headers=None, data=None, timeout=30
):
    """Make an authenticated request to Ops Manager with proper digest auth handling."""
    if headers is None:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

    logger.debug(f"Making {method} request to: {url}")
    logger.debug(f"Using username: {username}")
    logger.debug(f"SSL verification: {verify_ssl}")

    # Use a session to force digest authentication
    session = Session()
    session.auth = HTTPDigestAuth(username, apikey)
    session.verify = verify_ssl
    session.headers.update(headers)

    # Make a HEAD request first to force digest auth negotiation
    try:
        head_response = session.head(url, timeout=timeout)
        logger.debug(f"HEAD request status: {head_response.status_code}")
    except Exception as e:
        logger.debug(f"HEAD request failed: {e}")

    # Now make the actual request
    if method.upper() == "GET":
        response = session.get(url, timeout=timeout)
    elif method.upper() == "POST":
        response = session.post(url, data=data, timeout=timeout)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    logger.debug(f"Response status code: {response.status_code}")
    logger.debug(f"Response headers: {dict(response.headers)}")

    if response.status_code != 200:
        logger.error(f"Request failed with status {response.status_code}")
        logger.error(f"Response text: {response.text}")

    return response


def fetch_projects(host, username, apikey, verify_ssl=True):
    url = host + "/api/public/v1.0/groups"
    response = make_digest_request("GET", url, username, apikey, verify_ssl)
    response.raise_for_status()
    projects = response.json()
    logger.debug("Fetched Projects successfully")
    logger.debug(json.dumps(projects, indent=4))
    return projects
