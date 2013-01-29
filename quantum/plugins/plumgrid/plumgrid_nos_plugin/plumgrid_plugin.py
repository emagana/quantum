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


from quantum.db import api as db
from quantum.db import db_base_plugin_v2
from quantum.openstack.common import cfg
from quantum.openstack.common import log as logging
from quantum.plugins.plumgrid.plumgrid_nos_plugin import rest_connection


LOG = logging.getLogger(__name__)


nos_server_opts = [
    cfg.StrOpt('nos_server', default='localhost:8080',
               help=_("PLUMgrid NOS server to connect to")),
    cfg.StrOpt('username', default='username',
               help=_("PLUMgrid NOS admin username")),
    cfg.StrOpt('password', default='password',
               help=_("PLUMgrid NOS admin password")),
    cfg.IntOpt('servertimeout', default=5,
               help=_("PLUMgrid NOS server timeout")),
]


cfg.CONF.register_opts(nos_server_opts, "PLUMgridNOS")


class QuantumPluginPLUMgridV2(db_base_plugin_v2.QuantumDbPluginV2):

    def __init__(self):
        LOG.info(_('QuantumPluginPLUMgrid Status: Starting Plugin'))

        # Plugin DB initialization
        db.configure_db()

        # PLUMgrid NOS configuration
        nosplumgrid = cfg.CONF.PLUMgridNOS.nos_server
        nosusername = cfg.CONF.PLUMgridNOS.username
        nospassword = cfg.CONF.PLUMgridNOS.password
        timeout = cfg.CONF.PLUMgridNOS.servertimeout

        # PLUMgrid NOS info validation
        LOG.info(_('QuantumPluginPLUMgrid PLUMgrid NOS: %s'), nosplumgrid)
        if not nosplumgrid:
            LOG.error(_('QuantumPluginPLUMgrid Status: NOS server is not '
                        'included in config file'))

        LOG.debug(_('QuantumPluginPLUMgrid Status: Quantum server with '
                    'PLUMgrid Plugin has started'))

    def create_network(self, context, network):
        """
        Create network core Quantum API
        """

        LOG.debug(_('QuantumPluginPLUMgrid Status: create_network() called'))
        #from pudb import set_trace; set_trace()
        # Validate args
        tenant_id = self._get_tenant_id_for_create(context, network["network"])
        self.network_admin_state(network)

        # Plugin DB - Network Create
        net = super(QuantumPluginPLUMgridV2, self).create_network(context,
                                                                 network)
        LOG.debug(_('QuantumPluginPLUMgrid Status: %s, %s, %s'),
            tenant_id, network["network"], net["id"])

        # TODO: Create the PLUMgrid NOS REST API call
        """
        data = {
            "network": {
                "id": new_net["id"],
                "name": new_net["name"],
                }
        }
        headers = {}
        nos_url = 'NOS_URL'
        rest_connection.nos_rest_conn(nos_url, 'POST', data, headers)
        """
        # return created network
        return net

    def update_network(self, context, net_id, network):
        """
        Update network core Quantum API
        """

        LOG.debug(_("QuantumPluginPLUMgridV2.update_network() called"))
        self.network_admin_state(network)

        # Plugin DB - Network Update
        network_updated = super(QuantumPluginPLUMgridV2, self).update_network(
            context, net_id, network)

        # TODO: Update network on network controller
        # return updated network
        return network_updated

    def delete_network(self, context, net_id):
        """
        Delete network core Quantum API
        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: delete_network() called"))

        # TODO: Delete network on network controller
        net = super(QuantumPluginPLUMgridV2, self).get_network(context, net_id)
        tenant_id = net["tenant_id"]

        # Plugin DB - Network Delete
        result_from_net_delete = super(QuantumPluginPLUMgridV2,
            self).delete_network(context, net_id)

        return result_from_net_delete

    def create_port(self, context, port):
        """
        Create port core Quantum API
        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: create_port() called"))

        # Plugin DB - Port Create
        port["port"]["admin_state_up"] = False
        new_port = super(QuantumPluginPLUMgridV2, self).create_port(context,
            port)

        # TODO: Create port on PLUMgrid NOS Container

        # Set port state up and return that port
        port_update = {"port": {"admin_state_up": True}}
        return super(QuantumPluginPLUMgridV2, self).update_port(context,
            new_port["id"], port_update)

    def update_port(self, context, port_id, port):
        """
        Update port core Quantum API

        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: update_port() called"))

        # Validate Args
        orig_port = super(QuantumPluginPLUMgridV2, self).get_port(context,
            port_id)
        if orig_port:
            # Plugin DB - Port Update
            new_port = super(QuantumPluginPLUMgridV2, self).update_port(
                context, port_id, port)
        # TODO: Update port on PLUMgrid NOS

        # return new_port
        return new_port

    def delete_port(self, context, port_id):
        """
        Delete port core Quantum API
        """

        LOG.debug(_("QuantumPluginPLUMgrid Status: delete_port() called"))

        # Plugin DB - Port Delete
        super(QuantumPluginPLUMgridV2, self).delete_port(context, port_id)

        # TODO: Delete port from PLUMgrid NOS

    def network_admin_state(self, network):
        if network["network"].get("admin_state_up"):
            network_name = network["network"]["name"]
            if network["network"]["admin_state_up"] is False:
                LOG.warning(_("Network with admin_state_up=False are not yet "
                          "supported by this plugin. Ignoring setting for "
                          "network %s"), network_name)
