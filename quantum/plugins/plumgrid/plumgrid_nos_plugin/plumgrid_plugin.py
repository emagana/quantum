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
from quantum.plugins.plumgrid.common import exceptions as plum_excep
from quantum.plugins.plumgrid.plumgrid_nos_plugin import plumgrid_nos_snippets
from quantum.plugins.plumgrid.plumgrid_nos_plugin import rest_connection
from quantum.plugins.plumgrid.plumgrid_nos_plugin.plumgrid_plugin_version \
    import (VERSION)


LOG = logging.getLogger(__name__)


nos_server_opts = [
    cfg.StrOpt('nos_server', default='localhost',
        help=_("PLUMgrid NOS server to connect to")),
    cfg.StrOpt('nos_server_port', default='8080',
        help=_("PLUMgrid NOS server port to connect to")),
    cfg.StrOpt('username', default='username',
        help=_("PLUMgrid NOS admin username")),
    cfg.StrOpt('password', default='password',
        help=_("PLUMgrid NOS admin password")),
    cfg.IntOpt('servertimeout', default=5,
        help=_("PLUMgrid NOS server timeout")),
    ]


cfg.CONF.register_opts(nos_server_opts, "PLUMgridNOS")
# PLUMgrid NOS configuration
nos_plumgrid = cfg.CONF.PLUMgridNOS.nos_server
nos_port = cfg.CONF.PLUMgridNOS.nos_server_port
timeout = cfg.CONF.PLUMgridNOS.servertimeout
rest_conn = rest_connection.RestConnection(nos_plumgrid, nos_port, timeout)
snippets = plumgrid_nos_snippets.dataNOSPLUMgrid()

# TODO: (Edgar) These are placeholders for next PLUMgrid release
nos_username = cfg.CONF.PLUMgridNOS.username
nos_password = cfg.CONF.PLUMgridNOS.password


class QuantumPluginPLUMgridV2(db_base_plugin_v2.QuantumDbPluginV2):

    def __init__(self):
        LOG.info(_('QuantumPluginPLUMgrid Status: Starting Plugin'))

        # Plugin DB initialization
        db.configure_db()

        # PLUMgrid NOS info validation
        LOG.info(_('QuantumPluginPLUMgrid PLUMgrid NOS: %s'), nos_plumgrid)
        if not nos_plumgrid:
            LOG.error(_('QuantumPluginPLUMgrid Status: NOS server is not '
                        'included in config file'))

        LOG.debug(_('QuantumPluginPLUMgrid Status: Quantum server with '
                    'PLUMgrid Plugin has started'))

    def create_network(self, context, network):
        """
        Create network core Quantum API
        """

        LOG.debug(_('QuantumPluginPLUMgrid Status: create_network() called'))

        # Plugin DB - Network Create and validation
        tenant_id = self._get_tenant_id_for_create(context, network["network"])
        self.network_admin_state(network)
        net = super(QuantumPluginPLUMgridV2, self).create_network(context,
            network)

        try:
            LOG.debug(_('QuantumPluginPLUMgrid Status: %s, %s, %s'),
                tenant_id, network["network"], net["id"])
            nos_url = snippets.BASE_NOS_URL + net["id"]
            headers = {}
            body_data = snippets.create_domain_body_data(tenant_id)
            rest_conn.nos_rest_conn(nos_url, 'PUT', body_data, headers)

        except Exception:
            err_message = _("PLUMgrid NOS communication failed")
            raise plum_excep.PLUMgridException(err_message)

        # return created network
        return net

    def update_network(self, context, net_id, network):
        """
        Update network core Quantum API
        """

        LOG.debug(_("QuantumPluginPLUMgridV2.update_network() called"))
        self.network_admin_state(network)
        tenant_id = self._get_tenant_id_for_create(context, network["network"])

        # Plugin DB - Network Update
        network_updated = super(QuantumPluginPLUMgridV2, self).update_network(
            context, net_id, network)

        try:
            # PLUMgrid Server does not support updating resources yet
            nos_url = snippets.BASE_NOS_URL + net_id
            headers = {}
            body_data = {}
            rest_conn.nos_rest_conn(nos_url, 'DELETE', body_data, headers)
            nos_url = snippets.BASE_NOS_URL + network_updated["id"]
            body_data = snippets.create_domain_body_data(tenant_id)
            rest_conn.nos_rest_conn(nos_url, 'PUT', body_data, headers)
        except Exception:
            err_message = _("PLUMgrid NOS communication failed")
            raise plum_excep.PLUMgridException(err_message)

        # return updated network
        return network_updated

    def delete_network(self, context, net_id):
        """
        Delete network core Quantum API
        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: delete_network() called"))

        # TODO: Delete network on network controller
        net = super(QuantumPluginPLUMgridV2, self).get_network(context, net_id)

        # Plugin DB - Network Delete
        net_deleted = super(QuantumPluginPLUMgridV2,
            self).delete_network(context, net_id)

        try:
            nos_url = snippets.BASE_NOS_URL + net_id
            headers = {}
            body_data = {}
            rest_conn.nos_rest_conn(nos_url, 'DELETE', body_data, headers)
        except Exception:
            err_message = _("PLUMgrid NOS communication failed")
            raise plum_excep.PLUMgridException(err_message)

    def create_port(self, context, port):
        """
        Create port core Quantum API
        """
        LOG.debug(_("QuantumPluginPLUMgrid Status: create_port() called"))

        # Plugin DB - Port Create
        port["port"]["admin_state_up"] = False
        new_port = super(QuantumPluginPLUMgridV2, self).create_port(context,
            port)

        # TODO: Create port on PLUMgrid NOS

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

    def create_subnet(self, context, subnet):
        """
        Create subnet core Quantum API
        """

        LOG.debug(_("QuantumPluginPLUMgrid Status: create_subnet() called"))
        # Plugin DB - Subnet Delete
        subnet = super(QuantumPluginPLUMgridV2, self).create_subnet(context,
            subnet)
        subnet_details = self._get_subnet(context, subnet["id"])
        net_id = subnet_details["network_id"]
        tenant_id = subnet_details["tenant_id"]
        net = super(QuantumPluginPLUMgridV2, self).get_network(context,
            net_id)
        try:
            nos_url = snippets.BASE_NOS_URL + net["id"]
            headers = {}
            body_data = snippets.create_network_body_data(tenant_id)
            rest_conn.nos_rest_conn(nos_url, 'PUT', body_data, headers)
        except Exception:
            err_message = _("PLUMgrid NOS communication failed: ")
            raise plum_excep.PLUMgridException(err_message)

        return subnet

    def delete_subnet(self, context, subnet_id):
        """
        Delete subnet core Quantum API
        """

        LOG.debug(_("QuantumPluginPLUMgrid Status: delete_subnet() called"))
        #Collecting subnet info
        subnet_details = self._get_subnet(context, subnet_id)

        # Plugin DB - Subnet Delete
        del_subnet = super(QuantumPluginPLUMgridV2, self).delete_subnet(
            context, subnet_id)
        try:
            headers = {}
            body_data = {}
            net_id = subnet_details["network_id"]
            self.cleaning_nos_subnet_structure(body_data, headers, net_id)
        except Exception:
            err_message = _("PLUMgrid NOS communication failed: ")
            raise plum_excep.PLUMgridException(err_message)

        return del_subnet

    def update_subnet(self, context, subnet_id, subnet):
        """
        Update subnet core Quantum API
        """

        LOG.debug(_("update_subnet() called"))
        #Collecting subnet info
        subnet_details = self._get_subnet(context, subnet_id)
        net_id = subnet_details["network_id"]
        tenant_id = subnet_details["tenant_id"]
        try:
            # PLUMgrid Server does not support updating resources yet
            headers = {}
            body_data = {}
            self.cleaning_nos_subnet_structure(body_data, headers, net_id)
            nos_url = snippets.BASE_NOS_URL + net_id
            body_data = snippets.create_network_body_data(tenant_id)
            rest_conn.nos_rest_conn(nos_url, 'PUT', body_data, headers)

        except Exception:
            err_message = _("PLUMgrid NOS communication failed: ")
            raise plum_excep.PLUMgridException(err_message)

        return super(QuantumPluginPLUMgridV2, self).update_subnet(
            context, subnet_id, subnet)

    """
    Extension API implementation
    """
    # TODO: (Edgar) Complete extensions for PLUMgrid

    """
    Internal PLUMgrid fuctions
    """

    def get_plugin_version(self):
        return VERSION

    def cleaning_nos_subnet_structure(self, body_data, headers, net_id):
        domain_structure = ['/properties', '/link', '/ne']
        for structure in domain_structure:
            nos_url = snippets.BASE_NOS_URL + net_id + structure
            rest_conn.nos_rest_conn(nos_url, 'DELETE', body_data, headers)

    def network_admin_state(self, network):
        if network["network"].get("admin_state_up"):
            network_name = network["network"]["name"]
            if network["network"]["admin_state_up"] is False:
                LOG.warning(_("Network with admin_state_up=False are not yet "
                              "supported by this plugin. Ignoring setting for "
                              "network %s"), network_name)
