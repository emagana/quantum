# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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


import httplib

from nova import exception
from nova import log as logging
from nova import utils


LOG = logging.getLogger(__name__)


class LibvirtPLUMgridVIFDriver(LibvirtBridgeDriver):
    def __init__(self, **kwargs):
        self.smart_edge_command = '/opt/pg/bin/0/ifc_ctl'
        super(LibvirtPLUMgridVIFDriver, self).__init__()
        LOG.debug(_("Libvirt PLUMgrid VIF Driver Status: driver started"))

    def plug(self, instance, vif):
        LOG.debug(_("Libvirt PLUMgrid VIF Driver Status: plug() called"))
        network, mapping = vif
        result = super(LibvirtPLUMgridVIFDriver, self).plug(
            instance, vif)
        iface_id = mapping['vif_uuid']
        dev = self.get_dev_name(iface_id)
        try:
            utils.execute(self.smart_edge_command, '.', 'add_port', dev)
            utils.execute(self.smart_edge_command, '.', 'ifup', dev,
                'access_vm', mapping['label'], iface_id)
        except exception.ProcessExecutionError:
            LOG.exception(_("Libvirt PLUMgrid VIF Driver Error: %s") % dev)
        return result

    def unplug(self, instance, vif):
        LOG.debug(_("QuantumPlugin VIF Driver Status: unplug() called"))
        network, mapping = vif
        try:
            utils.execute(self.smart_edge_command, '.', 'ifdown', dev,
                'access_vm', mapping['label'], iface_id)
            utils.execute(self.smart_edge_command, '.', 'del_port', dev)
        except exception.ProcessExecutionError:
            LOG.exception(_("Libvirt PLUMgrid VIF Driver Error: %s") % dev)
        super(LibvirtPLUMgridVIFDriver, self).unplug(instance, network,
            mapping)

    def get_dev_name(self, iface_id):
        return "tap" + iface_id[0:11]
