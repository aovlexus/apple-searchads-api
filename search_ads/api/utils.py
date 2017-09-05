import contextlib

import os
import requests
from decouple import config

from tempfile import NamedTemporaryFile


@contextlib.contextmanager
def set_env(**environ):
    """
    Temporarily set the process environment variables.

    >>> with set_env(PLUGINS_DIR=u'test/plugins'):
    ...   "PLUGINS_DIR" in os.environ
    True

    >>> "PLUGINS_DIR" in os.environ
    False

    :type environ: dict[str, unicode]
    :param environ: Environment variables to set
    """
    old_environ = dict(os.environ)
    os.environ.update(environ)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_environ)


def api_call(endpoint, headers={}, json_data={}, method=requests.get,
             api_version='v1', limit=1000, offset=0, org_id=None,
             verbose=False):
    endpoint = "{}/{}".format(api_version, endpoint)
    # print("Endpoint:", endpoint)
    # print("Data:", json_data)

    temp_pem = NamedTemporaryFile(suffix='.pem')
    temp_key = NamedTemporaryFile(suffix='.key')

    pem_env_var = config('SEARCH-ADS-PEM')
    key_env_var = config('SEARCH-ADS-KEY')

    try:
        if pem_env_var.endswith('.pem'):  # env is the name of file
            call_kwargs = {
                "cert": (
                    pem_env_var,
                    key_env_var
                ),
                "headers": headers,
            }
        else:   # env var is the key explicit
            pem_lines = pem_env_var.split("\\n")
            temp_pem.writelines(["%s\n" % item for item in pem_lines])
            temp_pem.flush()  # ensure all data written

            key_lines = key_env_var.split("\\n")
            temp_key.writelines(["%s\n" % item for item in key_lines])
            temp_key.flush()  # ensure all data written

            call_kwargs = {
                "cert": (
                    temp_pem.name,
                    temp_key.name
                ),
                "headers": headers,
            }
        if json_data:
            call_kwargs['json'] = json_data
        if org_id:
            call_kwargs['headers']["Authorization"] = "orgId={org_id}".format(
                org_id=org_id)
        req = method(
            "https://api.searchads.apple.com/api/{endpoint}".format(
                endpoint=endpoint),
            **call_kwargs
        )
    finally:
        # Automatically cleans up the file
        temp_pem.close()
        temp_key.close()

    if verbose:
        print(req.text)
    return req.json()


def api_get(endpoint, api_version='v1', limit=1000, offset=0, org_id=None,
            verbose=False):
    return api_call(
        endpoint="{endpoint}?limit={limit}&offset={offset}".format(
            endpoint=endpoint, limit=limit, offset=offset),
        api_version=api_version,
        limit=limit,
        offset=offset,
        org_id=org_id,
        verbose=verbose
    )


def api_put(endpoint, data, api_version='v1', org_id=None, verbose=False):
    return api_call(
        endpoint,
        json_data=data,
        method=requests.put,
        api_version=api_version,
        org_id=org_id,
        verbose=verbose
    )


def api_post(endpoint, data, api_version='v1', org_id=None, verbose=False):
    return api_call(
        endpoint,
        json_data=data,
        method=requests.post,
        api_version=api_version,
        org_id=org_id,
        verbose=verbose
    )
