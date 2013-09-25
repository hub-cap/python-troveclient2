from troveclient.openstack.common.apiclient import client
from troveclient import auth

def create_http_client(username=None, password=None, project_id=None, auth_url='', insecure=False, region_name=None,
		       tenant_id=None, extensions=None,service_name=None, service_type=None,
                  endpoint_type=None, verify=None, cacert=None, timeout=None,
                  http_log_debug=None, retries=None, database_service_name=None):
        auth_type = auth.KeystoneV2AuthPlugin(username=username,
                                           password=password,
                                           tenant_name=project_id,
                                           auth_url=auth_url)
        verify = not insecure
        return auth.CustomClient(auth_type, region_name=region_name,
                                             endpoint_type=endpoint_type,
                                             verify=verify, cert=cacert,
                                             timeout=timeout,
                                             debug=http_log_debug,
                                             user_agent='python-troveclient')

def Client(version, *args, **kwargs):
    version_map = {
        '1': 'troveclient.v1.client.Client',
    }
    client_class = client.BaseClient.get_class('database', version, version_map)
    print args
    print kwargs
    http_client = create_http_client(*args, **kwargs)
    return client_class(http_client, extensions=kwargs.get('extensions'))
