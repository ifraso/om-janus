import json

import requests
from requests.auth import HTTPDigestAuth

from janus.logging import logger


def fetch_projects(host, username, apikey):
    response = requests.get(
        host + "/api/public/v1.0/groups", auth=HTTPDigestAuth(username, apikey)
    )
    response.raise_for_status()
    projects = response.json()
    logger.debug("Fetched Projects ...")
    logger.debug(json.dumps(projects, indent=4))
    return projects
