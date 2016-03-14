#!/usr/bin/env python
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.


import eventlet

import sys
import warnings

warnings.simplefilter('once', DeprecationWarning)

from oslo.config import cfg
from birdie.common import log as logging

from birdie import i18n
i18n.enable_lazy()

# Need to register global_opts
from birdie.common import config  # noqa
from birdie import service
from birdie import utils
from birdie import version


CONF = cfg.CONF


def main():
    CONF(sys.argv[1:], project='v2v',
         version=version.version_string())
    logging.setup(CONF, "v2v")
    #create service
    server = service.Service.create(binary='v2v-migration')
    #running service
    service.serve(server)
    #listen service
    service.wait()
