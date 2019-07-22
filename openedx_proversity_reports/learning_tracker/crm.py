"""
CRM salesforce interface
"""

from collections import OrderedDict
from urllib import urlencode

import requests


class CrmInterface:

    def __init__(self, *args, **kwargs):
        self.client_id = kwargs['client_id']
        self.grant_type = kwargs['grant_type']
        self.client_secret = kwargs['client_secret']
        self.username = kwargs['username']
        self.password = kwargs['password']
        self.security_token = kwargs['security_token']

    def generate_token(self, url, client_id, client_secret, username, password, security_token):  # pylint: disable=too-many-arguments
        """
        This method generate an authentication token for SalesForce
        """
        # pylint: disable=unused-argument

        payload = urlencode(
            OrderedDict(
                grant_type=self.grant_type,
                client_id=self.client_id,
                client_secret=self.client_secret,
                username=self.username,
                password="{}{}".format(self.password,self.security_token)
            )
        )

        headers = {'content-type': "application/x-www-form-urlencoded",}
        response = requests.request("POST", url, data=payload, headers=headers)

        if response.status_code == 200:
            print "request succes -- token obtained"
        else:
            print "request failure"
        return response
