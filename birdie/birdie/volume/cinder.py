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

"""
Handles all requests relating to volumes + cinder.
"""

import copy
import sys

from cinderclient import client as cinder_client
from cinderclient import exceptions as cinder_exception
from cinderclient.v1 import client as v1_client
from keystoneclient import exceptions as keystone_exception
from keystoneclient import session
from oslo.config import cfg
from oslo.utils import strutils
import six
import six.moves.urllib.parse as urlparse

from birdie.common import log as logging

from birdie import exception
from birdie.i18n import _
from birdie.i18n import _LW

cinder_opts = [
    cfg.StrOpt('catalog_info',
            default='volumev2:cinderv2:publicURL',
            help='Info to match when looking for cinder in the service '
                 'catalog. Format is: separated values of the form: '
                 '<service_type>:<service_name>:<endpoint_type>'),
    cfg.StrOpt('endpoint_template',
               help='Override service catalog lookup with template for cinder '
                    'endpoint e.g. http://localhost:8776/v1/%(project_id)s'),
    cfg.StrOpt('os_region_name',
               help='Region name of this node'),
    cfg.IntOpt('http_retries',
               default=3,
               help='Number of cinderclient retries on failed http calls'),
]

CONF = cfg.CONF
CINDER_OPT_GROUP = 'cinder'

# cinder_opts options in the DEFAULT group were deprecated in Juno
CONF.register_opts(cinder_opts, group=CINDER_OPT_GROUP)


deprecated = {'timeout': [cfg.DeprecatedOpt('http_timeout',
                                            group=CINDER_OPT_GROUP)],
              'cafile': [cfg.DeprecatedOpt('ca_certificates_file',
                                           group=CINDER_OPT_GROUP)],
              'insecure': [cfg.DeprecatedOpt('api_insecure',
                                             group=CINDER_OPT_GROUP)]}

session.Session.register_conf_options(CONF,
                                      CINDER_OPT_GROUP,
                                      deprecated_opts=deprecated)

LOG = logging.getLogger(__name__)

_SESSION = None
_V1_ERROR_RAISED = False


def reset_globals():
    """Testing method to reset globals.
    """
    global _SESSION
    _SESSION = None


def cinderclient(context):
    global _SESSION
    global _V1_ERROR_RAISED

    if not _SESSION:
        _SESSION = session.Session.load_from_conf_options(CONF,
                                                          CINDER_OPT_GROUP)

    url = None
    endpoint_override = None
    version = None

    auth = context.get_auth_plugin()
    service_type, service_name, interface = CONF.cinder.catalog_info.split(':')

    service_parameters = {'service_type': service_type,
                          'service_name': service_name,
                          'interface': interface,
                          'region_name': CONF.cinder.os_region_name}

    if CONF.cinder.endpoint_template:
        url = CONF.cinder.endpoint_template % context.to_dict()
        endpoint_override = url
    else:
        url = _SESSION.get_endpoint(auth, **service_parameters)

    # TODO(jamielennox): This should be using proper version discovery from
    # the cinder service rather than just inspecting the URL for certain string
    # values.
    version = get_cinder_client_version(url)

    if version == '1' and not _V1_ERROR_RAISED:
        msg = _LW('Cinder V1 API is deprecated as of the Juno '
                  'release, and Nova is still configured to use it. '
                  'Enable the V2 API in Cinder and set '
                  'cinder_catalog_info in nova.conf to use it.')
        LOG.warn(msg)
        _V1_ERROR_RAISED = True

    return cinder_client.Client(version,
                                session=_SESSION,
                                auth=auth,
                                endpoint_override=endpoint_override,
                                connect_retries=CONF.cinder.http_retries,
                                **service_parameters)


def _untranslate_volume_summary_view(context, vol):
    """Maps keys for volumes summary view."""
    d = {}
    d['id'] = vol.id
    d['status'] = vol.status
    d['size'] = vol.size
    d['availability_zone'] = vol.availability_zone
    d['created_at'] = vol.created_at

    # TODO(jdg): The calling code expects attach_time and
    #            mountpoint to be set. When the calling
    #            code is more defensive this can be
    #            removed.
    d['attach_time'] = ""
    d['mountpoint'] = ""

    if vol.attachments:
        att = vol.attachments[0]
        d['attach_status'] = 'attached'
        d['instance_uuid'] = att['server_id']
        d['mountpoint'] = att['device']
    else:
        d['attach_status'] = 'detached'
    # NOTE(dzyu) volume(cinder) v2 API uses 'name' instead of 'display_name',
    # and use 'description' instead of 'display_description' for volume.
    if hasattr(vol, 'display_name'):
        d['display_name'] = vol.display_name
        d['display_description'] = vol.display_description
    else:
        d['display_name'] = vol.name
        d['display_description'] = vol.description
    # TODO(jdg): Information may be lost in this translation
    d['volume_type_id'] = vol.volume_type
    d['snapshot_id'] = vol.snapshot_id
    d['bootable'] = strutils.bool_from_string(vol.bootable)
    d['volume_metadata'] = {}
    for key, value in vol.metadata.items():
        d['volume_metadata'][key] = value

    if hasattr(vol, 'volume_image_metadata'):
        d['volume_image_metadata'] = copy.deepcopy(vol.volume_image_metadata)

    return d

def translate_volume_exception(method):
    """Transforms the exception for the volume but keeps its traceback intact.
    """
    def wrapper(self, ctx, volume_id, *args, **kwargs):
        try:
            res = method(self, ctx, volume_id, *args, **kwargs)
        except (cinder_exception.ClientException,
                keystone_exception.ClientException):
            exc_type, exc_value, exc_trace = sys.exc_info()
            if isinstance(exc_value, (keystone_exception.NotFound,
                                      cinder_exception.NotFound)):
                exc_value = exception.VolumeNotFound(volume_id=volume_id)
            elif isinstance(exc_value, (keystone_exception.BadRequest,
                                        cinder_exception.BadRequest)):
                exc_value = exception.InvalidInput(
                    reason=six.text_type(exc_value))
            raise exc_value, None, exc_trace
        except (cinder_exception.ConnectionError,
                keystone_exception.ConnectionError):
            exc_type, exc_value, exc_trace = sys.exc_info()
            exc_value = exception.CinderConnectionFailed(
                reason=six.text_type(exc_value))
            raise exc_value, None, exc_trace
        return res
    return wrapper


def get_cinder_client_version(url):
    """Parse cinder client version by endpoint url.

    :param url: URL for cinder.
    :return: str value(1 or 2).
    """
    # FIXME(jamielennox): Use cinder_client.get_volume_api_from_url when
    # bug #1386232 is fixed.
    valid_versions = ['v1', 'v2']
    scheme, netloc, path, query, frag = urlparse.urlsplit(url)
    components = path.split("/")

    for version in valid_versions:
        if version in components:
            return version[1:]

    msg = "Invalid client version '%s'. must be one of: %s" % (
        (version, ', '.join(valid_versions)))
    raise cinder_exception.UnsupportedVersion(msg)


class API(object):
    """API for interacting with the volume manager."""

    @translate_volume_exception
    def get(self, context, volume_id):
        item = cinderclient(context).volumes.get(volume_id)
        return _untranslate_volume_summary_view(context, item)

    def get_all(self, context, search_opts=None):
        search_opts = search_opts or {}
        items = cinderclient(context).volumes.list(detailed=True,
                                                   search_opts=search_opts)

        rval = []

        for item in items:
            rval.append(_untranslate_volume_summary_view(context, item))

        return rval



    def migrate_volume_completion(self, context, old_volume_id, new_volume_id,
                                  error=False):
        return cinderclient(context).volumes.migrate_volume_completion(
            old_volume_id, new_volume_id, error)


  
