# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
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

"""Base Manager class.

Managers are responsible for a certain aspect of the system.  It is a logical
grouping of code relating to a portion of the system.  In general other
components should be using the manager to make changes to the components that
it is responsible for.

For example, other components that need to deal with volumes in some way,
should do so by calling methods on the VolumeManager instead of directly
changing fields in the database.  This allows us to keep all of the code
relating to volumes in the same place.

We have adopted a basic strategy of Smart managers and dumb data, which means
rather than attaching methods to data objects, components should call manager
methods that act on the data.

Methods on managers that can be executed locally should be called directly. If
a particular method must execute on a remote host, this should be done via rpc
to the service that wraps the manager

Managers should be responsible for most of the db access, and
non-implementation specific data.  Anything implementation specific that can't
be generalized should be done by the Driver.

In general, we prefer to have one manager with multiple drivers for different
implementations, but sometimes it makes sense to have multiple managers.  You
can think of it this way: Abstract different overall strategies at the manager
level(FlatNetwork vs VlanNetwork), and different implementations at the driver
level(LinuxNetDriver vs CiscoNetDriver).

Managers will often provide methods for initial setup of a host or periodic
tasks to a wrapping service.

This module provides Manager, a base class for managers.

"""


from oslo.config import cfg
import oslo.messaging as messaging

from birdie.common import log as logging
from birdie.common import periodic_task

from birdie import version
from birdie import rpc


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class Manager(periodic_task.PeriodicTasks):
    # Set RPC API version to 1.0 by default.
    RPC_API_VERSION = '1.0'

    target = messaging.Target(version=RPC_API_VERSION)

    def __init__(self, host=None, db_driver=None, service_name='undefined'):
        if not host:
            host = CONF.host
        self.host = host
        self.additional_endpoints = []
        self.service_name = service_name
        self.notifier = rpc.get_notifier(self.service_name, self.host)
        super(Manager, self).__init__()

    def periodic_tasks(self, context, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    def init_host(self):
        """Handle initialization if this is a standalone service.

        A hook point for services to execute tasks before the services are made
        available (i.e. showing up on RPC and starting to accept RPC calls) to
        other components.  Child classes should override this method.

        """
        pass

    def init_host_with_rpc(self):
        """A hook for service to do jobs after RPC is ready.

        Like init_host(), this method is a hook where services get a chance
        to execute tasks that *need* RPC. Child classes should override
        this method.

        """
        pass

    def service_version(self, context):
        return version.version_string()

    def service_config(self, context):
        config = {}
        for key in CONF:
            config[key] = CONF.get(key, None)
        return config

