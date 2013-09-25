from troveclient.openstack.common.apiclient import client
from troveclient import auth

from troveclient.v1 import instances


class Client(client.BaseClient):
    def __init__(self, http_client, extensions=None):
        super(Client, self).__init__(http_client, extensions=extensions)

        self.instances = instances.Instances(self)
    
    def authenticate(self):
        self.http_client.authenticate()

    def get_database_api_version_from_endpoint(self):
        return "1"








