import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def get_base_session():
    session = requests.Session()
    retry = Retry(
        total=10,
        backoff_factor=1,
        status_forcelist=[403, 503],
        allowed_methods=["GET", "POST"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session
