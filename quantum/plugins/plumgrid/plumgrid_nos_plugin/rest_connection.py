# vim: tabstop=4 shiftwidth=4 softtabstop=4
# Copyright 2013 PLUMgrid, Inc. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# @author: Edgar Magana, emagana@plumgrid.com, PLUMgrid, Inc.

"""
Quantum PLUMgrid Plug-in for PLUMgrid Virtual Technology
This plugin will forward authenticated REST API calls
to the Network Operating System by PLUMgrid called NOS
...
"""

import httplib
import json
import urllib2

from quantum.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class RestConnection(object):
    """REST Connection to PLUMgrid NOS Server."""

    def __init__(self, server, port, timeout):
        self.server = server
        self.port = port
        self.timeout = timeout

    def nos_rest_conn(self, nos_url, action, data, headers):
        uri = nos_url
        body = json.dumps(data)
        if not headers:
            headers = {}
        headers['Content-type'] = 'application/json'
        headers['Accept'] = 'application/json'
        headers['QuantumProxy-Agent'] = self.name

        LOG.debug(_("ServerProxy: server=%(server)s, port=%(port)d, "
                    "ssl=%(ssl)r, action=%(action)s"),
            {'server': self.server, 'port': self.port,
             'action': action})
        LOG.debug(_("ServerProxy: resource=%(resource)s, data=%(data)r, "
                    "headers=%(headers)r"), locals())

        conn = httplib.HTTPConnection(
                self.server, self.port, timeout=self.timeout)
        if conn is None:
            LOG.error(_('ServerProxy: Could not establish HTTP '
                            'connection'))
            return None

        try:
            conn.request(action, nos_url, body, headers)
            response = conn.getresponse()
            respstr = response.read()
            respdata = respstr
            LOG.debug(_("ServerProxy Connection Data: %s, %s, %s"),
                response, respstr, respdata)
            if response.status in self.success_codes:
                try:
                    #respdata = json.loads(respstr)
                    pass
                except ValueError:
                    # response was not JSON, ignore the exception
                    pass
            ret = (response.status, response.reason, respstr, respdata)
        except urllib2.HTTPError, e:
            LOG.error(_('ServerProxy: %(action)s failure, %(e)r'), locals())
            ret = 0, None, None, None
        conn.close()
        LOG.debug(_("ServerProxy: status=%(status)d, reason=%(reason)r, "
                    "ret=%(ret)s, data=%(data)r"), {'status': ret[0],
                                                    'reason': ret[1],
                                                    'ret': ret[2],
                                                    'data': ret[3]})
        return ret
