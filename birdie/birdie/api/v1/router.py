# Copyright 2011 OpenStack Foundation
# Copyright 2011 United States Government as represented by the
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

"""
WSGI middleware for Hybrid-birdie API.
"""

from birdie.common import log as logging

from birdie.api import extensions
import birdie.api.wsgi

from birdie.api.v1 import services



LOG = logging.getLogger(__name__)


class APIRouter(birdie.api.wsgi.APIRouter):
    """Routes requests on the API to the appropriate controller and method."""
    ExtensionManager = extensions.ExtensionManager

    def _setup_routes(self, mapper, ext_mgr):
        LOG.debug("api service start")
        self.resources['services'] = services.create_resource(ext_mgr)
        mapper.resource("service", "services",
                        controller=self.resources['services'],
                        collection={'detail': 'GET'},
                        member={'action': 'POST'})

       
