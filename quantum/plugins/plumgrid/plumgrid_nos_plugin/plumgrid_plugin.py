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

        # validate config
        LOG.info(_('QuantumPluginPLUMgrid PLUMgrid NOS: %s'), nosplumgrid)
        if not nosplumgrid:
            LOG.error(_('QuantumPluginPLUMgrid Status: NOS server is not '
                        'included in config file'))

        LOG.debug(_('QuantumPluginPLUMgrid Status: Quantum server with '
                    'PLUMgrid Plugin has started'))

    def create_network(self, context, network):
        """Create a network, which represents an L2 network segment which
        can have a set of subnets and ports associated with it.
        :param context: quantum api request context
        :param network: dictionary describing the network

        :returns: a sequence of mappings with the following signature:
        {
            "id": UUID representing the network.
            "name": Human-readable name identifying the network.
            "tenant_id": Owner of network. NOTE: only admin user can specify
                         a tenant_id other than its own.
            "admin_state_up": Sets admin state of network.
                              if down, network does not forward packets.
            "status": Indicates whether network is currently operational
                      (values are "ACTIVE", "DOWN", "BUILD", and "ERROR")
            "subnets": Subnets associated with this network.
        }
        """

        LOG.debug(_('QuantumPluginPLUMgrid Status: create_network() called'))
        #from pudb import set_trace; set_trace()
        # Validate args
        tenant_id = self._get_tenant_id_for_create(context, network["network"])
        self.network_admin_state(network)

        # create in DB
        net = super(QuantumPluginPLUMgridV2, self).create_network(context,
                                                                 net)
        LOG.debug(_('QuantumPluginPLUMgrid Status: %s, %s, %s'),
            tenant_id, net_name, net["id"])

        # TODO: Create the PLUMgrid NOS REST API call
        data = {
            "network": {
                "id": new_net["id"],
                "name": new_net["name"],
                }
        }
        headers = {}
        nos_url = 'NOS_URL'
        rest_connection.nos_rest_conn(nos_url, 'POST', data, headers)
        # return created network
        return net

    def update_network(self, context, net_id, network):
        """Updates the properties of a particular Virtual Network.
        :param context: quantum api request context
        :param net_id: uuid of the network to update
        :param network: dictionary describing the updates

        :returns: a sequence of mappings with the following signature:
        {
            "id": UUID representing the network.
            "name": Human-readable name identifying the network.
            "tenant_id": Owner of network. NOTE: only admin user can
                         specify a tenant_id other than its own.
            "admin_state_up": Sets admin state of network.
                              if down, network does not forward packets.
            "status": Indicates whether network is currently operational
                      (values are "ACTIVE", "DOWN", "BUILD", and "ERROR")
            "subnets": Subnets associated with this network.
        }
        """

        LOG.debug(_("QuantumPluginPLUMgridV2.update_network() called"))
        self.network_admin_state(network)

        # update DB
        net = super(QuantumPluginPLUMgridV2, self).update_network(
            context, net_id, network)

        # TODO: Update network on network controller

        # return updated network
        return net

    def delete_network(self, context, net_id):
        """Delete a network.
        :param context: quantum api request context
        :param id: UUID representing the network to delete.

        :returns: None
        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: delete_network() called"))

        # TODO: Delete network on network controller
        net = super(QuantumPluginPLUMgridV2, self).get_network(context, net_id)
        tenant_id = net["tenant_id"]

        # Delete Network from DB
        super(QuantumPluginPLUMgridV2, self).delete_network(context,
                                                                     net_id)

    def create_port(self, context, port):
        """Create a port, which is a connection point of a device
        (e.g., a VM NIC) to attach to a L2 Quantum network.
        :param context: quantum api request context
        :param port: dictionary describing the port

        :returns:
        {
            "id": uuid represeting the port.
            "network_id": uuid of network.
            "tenant_id": tenant_id
            "mac_address": mac address to use on this port.
            "admin_state_up": Sets admin state of port. if down, port
                              does not forward packets.
            "status": dicates whether port is currently operational
                      (limit values to "ACTIVE", "DOWN", "BUILD", and "ERROR")
            "fixed_ips": list of subnet ID"s and IP addresses to be used on
                         this port
            "device_id": identifies the device (e.g., virtual server) using
                         this port.
        }
        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: create_port() called"))

        # Update DB
        port["port"]["admin_state_up"] = False
        new_port = super(QuantumPluginPLUMgridV2, self).create_port(context,
            port)

        # TODO: Create port on PLUMgrid NOS Container

        # Set port state up and return that port
        port_update = {"port": {"admin_state_up": True}}
        return super(QuantumPluginPLUMgridV2, self).update_port(context,
                                                           new_port["id"],
                                                           port_update)

    def update_port(self, context, port_id, port):
        """Update values of a port.
        :param context: quantum api request context
        :param id: UUID representing the port to update.
        :param port: dictionary with keys indicating fields to update.

        :returns: a mapping sequence with the following signature:
        {
            "id": uuid represeting the port.
            "network_id": uuid of network.
            "tenant_id": tenant_id
            "mac_address": mac address to use on this port.
            "admin_state_up": sets admin state of port. if down, port
                               does not forward packets.
            "status": dicates whether port is currently operational
                       (limit values to "ACTIVE", "DOWN", "BUILD", and "ERROR")
            "fixed_ips": list of subnet ID's and IP addresses to be used on
                         this port
            "device_id": identifies the device (e.g., virtual server) using
                         this port.
        }
        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: update_port() called"))

        # Validate Args
        orig_port = super(QuantumPluginPLUMgridV2, self).get_port(context,
            port_id)
        if orig_port:

            # Update DB
            new_port = super(QuantumPluginPLUMgridV2, self).update_port(
                context, port_id, port)
        # TODO: Update port on PLUMgrid NOS

        # return new_port
        return new_port

    def delete_port(self, context, port_id):
        """Delete a port.
        :param context: quantum api request context
        :param id: UUID representing the port to delete.

        :raises: exceptions.PortInUse
        :raises: exceptions.PortNotFound
        :raises: exceptions.NetworkNotFound
        :raises: RemoteRestError
        """

        LOG.debug(_("QuantumPluginPLUMgrid Status: delete_port() called"))

        # Delete from DB
        super(QuantumPluginPLUMgridV2, self).get_port(context, port_id)

        # TODO: Delete port from PLUMgrid NOS

    def create_subnet(self, context, subnet):
        """
        Create a subnet, which represents a range of IP addresses
        that can be allocated to devices.
        """
        LOG.debug(_("create_subnet() called"))
        super(QuantumPluginPLUMgridV2, self).create_subnet(context, subnet)
        # TODO: Create subnet in PLUMgrid NOS

    def update_subnet(self, context, id, subnet):
        """
        Updates the state of a subnet and returns the updated subnet
        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: update_subnet() called"))
        super(QuantumPluginPLUMgridV2, self).update_subnet(context, id, subnet)
        # TODO: Update subnet in PLUMgrid NOS

    def delete_subnet(self, context, id):
        """
        Deletes a subnet
        """
        LOG.debug(_("delete_subnet() called"))
        super(QuantumPluginPLUMgridV2, self).delete_subnet(context, id)

    def network_admin_state(self, network):
        net_name = network["network"]["name"]
        if network["network"]["admin_state_up"] is False:
            LOG.warning(_("Network with admin_state_up=False are not yet "
                          "supported by this plugin. Ignoring setting for "
                          "network %s"), net_name)
