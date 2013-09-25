import logging

from troveclient.openstack.common.apiclient import exceptions
from troveclient.openstack.common.apiclient import client

logger = logging.getLogger(__name__)


class CustomClient(client.HTTPClient):

    def client_request(self, client, method, url, **kwargs):
        """Send an http request using `client`'s endpoint and specified `url`.

        If request was rejected as unauthorized (possibly because the token is
        expired), issue one authorization attempt and send the request once
        again.

        :param client: instance of BaseClient descendant
        :param method: method of HTTP request
        :param url: URL of HTTP request
        :param kwargs: any other parameter that can be passed to
            `HttpClient.request`
        """

        # To send a request, we need a token and an endpoint.
        # There are several ways to retrieve them.
        # token:
        # - self.cached_token
        # - self.auth_response.token
        # endpoint:
        # - client.endpoint
        # - client.cache_endpoint
        # - self.endpoint
        # - self.auth_response.url_for()
        # All these fields can be set by auth_plugin during
        # authentication.

        url_for_args = {
            "endpoint_type": client.endpoint_type or self.endpoint_type,
            "service_type": client.service_type,
            "filter_attrs": (
                {"region": self.region_name}
                if self.region_name
                else {}
            )
        }

        def get_token_and_endpoint(silent):
            print "ZOMG %s" % self.auth_response
            token = self.cached_token or self.auth_response['access']['token']
            endpoint = (client.endpoint or client.cached_endpoint or
                        self.endpoint)
            if not endpoint:
                try:
                    endpoint = self.auth_response.url_for(**url_for_args)
                except exceptions.EndpointException:
                    if not silent:
                        raise
            return (token, endpoint)

        token, endpoint = get_token_and_endpoint(silent=True)
        just_authenticated = False
        if not (endpoint and token):
            self.authenticate()
            just_authenticated = True
            token, endpoint = get_token_and_endpoint(silent=False)
            if not (endpoint and token):
                raise exceptions.AuthorizationFailure(
                    "Cannot find endpoint or token for request")

        old_token_endpoint = (token, endpoint)
        kwargs.setdefault("headers", {})["X-Auth-Token"] = token
        client.cached_endpoint = endpoint
        # Perform the request once. If we get Unauthorized, then it
        # might be because the auth token expired, so try to
        # re-authenticate and try again. If it still fails, bail.
        try:
            return self.request(
                method, self.concat_url(endpoint, url), **kwargs)
        except exceptions.Unauthorized:
            if just_authenticated:
                raise
            client.cached_endpoint = None
            self.authenticate()
            token, endpoint = get_token_and_endpoint(silent=True)
            if (not (endpoint and token) or
                    old_token_endpoint == (endpoint, token)):
                raise
            client.cached_endpoint = endpoint
            kwargs["headers"]["X-Auth-Token"] = token
            return self.request(
                method, self.concat_url(endpoint, url), **kwargs)


class KeystoneV2AuthPlugin(object):
    auth_system = "keystone"
    opt_names = [
        "username",
        "password",
        "tenant_id",
        "tenant_name",
        "token",
        "auth_url",
    ]
    
    def __init__(self, auth_system=None, **kwargs):
        self.auth_system = auth_system or self.auth_system
        self.opts = dict((name, kwargs.get(name))
                        for name in self.opt_names)

    def authenticate(self, http_client):
        if not self.opts.get("auth_url"):
            raise exceptions.AuthPluginOptionsMissing(["auth_url"])
        if self.opts.get("token"):
            params = {"auth": {"token": {"id": self.opts.get("token")}}}
        elif self.opts.get("username") and self.opts.get("password"):
            params = {
                "auth": {
                    "passwordCredentials": {
                        "username": self.opts.get("username"),
                        "password": self.opts.get("password"),
                    }
                }
            }
        else:
            raise exceptions.AuthPluginOptionsMissing(
                [opt
                 for opt in "username", "password", "token"
                 if not self.opts.get(opt)])
        if self.opts.get("tenant_id"):
            params["auth"]["tenantId"] = self.opts.get("tenant_id")
        elif self.opts.get("tenant_name"):
            params["auth"]["tenantName"] = self.opts.get("tenant_name")
        try:
            body = http_client.request(
                "POST",
                http_client.concat_url(self.opts.get("auth_url"), "/tokens"),
                allow_redirects=True,
                json=params).json()
        except ValueError as ex:
            raise exceptions.AuthorizationFailure(ex)
        http_client.auth_response = body
