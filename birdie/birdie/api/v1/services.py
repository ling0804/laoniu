# Copyright 2011 Justin Santa Barbara
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

"""The birdie api."""

import ast

import webob
from webob import exc

from birdie.common import log as logging
from birdie.api import common
from birdie.api.wsgi import wsgi
from birdie import exception
from birdie.i18n import _, _LI
from birdie import utils

from birdie.api.views import services as services_view
from birdie import volume 
from birdie import compute
from birdie.server import api as server_api


LOG = logging.getLogger(__name__)


class ServiceController(wsgi.Controller):
    """The Volumes API controller for the OpenStack API."""

    def __init__(self, ext_mgr):
        self.ext_mgr = ext_mgr
        self.viewBulid = services_view.ViewBuilder()
        self.cinder_api = volume.API()
        self.nova_api = compute.API()
        self.server_api = server_api.MigrationAPI()
        super(ServiceController, self).__init__()

    def show(self, req, id):
        """Return data about the given resource."""
        context = req.environ['birdie.context']
        
        
        server = self.nova_api.get_server(context, id, privileged_user=True, timeout=5)
        return  self.viewBulid.show(server)

    def delete(self, req, id):
        """Delete resource."""
        LOG.debug("delete is start.")
        context = req.environ['birdie.context']
        self.server_api.get_all(context)
        return

    def index(self, req):
        """Returns a summary list of resource."""
        LOG.debug("index is start.")
        context = req.environ['birdie.context']
        #1. query info from server model
        vols = self.cinder_api.get_all(context)
        
        LOG.debug("index volumes: %s", str(vols))
        #2. transform result to UI needed object mode      
        return self.viewBulid.list(vols)

    def detail(self, req):
        """Returns a detailed list of resource."""
        LOG.debug("Detail is start.")
        
        context = req.environ['birdie.context']
        
        obj = {
            "resources": [{
                "id": "123",
                "name":"birdie-test",
            },
                          
            {
                "id": "1234",
                "name":"birdie-test2",
            }] 
        }
          
        return obj

    def create(self, req, body):
        """Creates a new resource."""
        pass


    def update(self, req, id, body):
        """Update a resource."""
        context = req.environ['birdie.context']

        pass


def create_resource(ext_mgr):
    return wsgi.Resource(ServiceController(ext_mgr))
