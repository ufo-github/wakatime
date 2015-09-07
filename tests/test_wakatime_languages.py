# -*- coding: utf-8 -*-


from wakatime.main import execute
from wakatime.packages import requests

import os
import time
import sys
from wakatime.compat import u
from wakatime.packages.requests.models import Response
from . import utils

try:
    from .packages import simplejson as json
except (ImportError, SyntaxError):
    import json
try:
    from mock import ANY
except ImportError:
    from unittest.mock import ANY


class LanguagesTestCase(utils.TestCase):
    patch_these = [
        'wakatime.packages.requests.adapters.HTTPAdapter.send',
        'wakatime.offlinequeue.Queue.push',
        ['wakatime.offlinequeue.Queue.pop', None],
        'wakatime.session_cache.SessionCache.save',
        'wakatime.session_cache.SessionCache.delete',
        ['wakatime.session_cache.SessionCache.get', requests.session],
    ]

    def test_python_dependencies_detected(self):
        response = Response()
        response.status_code = 0
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        entity = 'tests/samples/codefiles/python.py'
        config = 'tests/samples/sample.cfg'

        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)
        self.assertEquals(sys.stdout.getvalue(), '')
        self.assertEquals(sys.stderr.getvalue(), '')

        self.patched['wakatime.session_cache.SessionCache.get'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.delete'].assert_called_once_with()
        self.patched['wakatime.session_cache.SessionCache.save'].assert_not_called()

        heartbeat = {
            'language': u('Python'),
            'lines': 27,
            'entity': os.path.realpath(entity),
            'project': u(os.path.basename(os.path.realpath('.'))),
            'dependencies': ANY,
            'branch': os.environ.get('TRAVIS_COMMIT', ANY),
            'time': float(now),
            'type': 'file',
        }
        stats = {
            u('cursorpos'): None,
            u('dependencies'): ANY,
            u('language'): u('Python'),
            u('lineno'): None,
            u('lines'): 27,
        }
        expected_dependencies = ['wakatime', 'mock', 'django', 'simplejson', 'os']
        expected_dependencies = ['wakatime', 'mock', 'django', 'simplejson', 'os']

        self.patched['wakatime.offlinequeue.Queue.push'].assert_called_once_with(heartbeat, ANY, None)
        for dep in expected_dependencies:
            self.assertIn(dep, self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['dependencies'])
        self.assertEquals(stats, json.loads(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][1]))
        self.patched['wakatime.offlinequeue.Queue.pop'].assert_not_called()

    def test_language_detected_for_header_file(self):
        response = Response()
        response.status_code = 500
        self.patched['wakatime.packages.requests.adapters.HTTPAdapter.send'].return_value = response

        now = u(int(time.time()))
        config = 'tests/samples/sample.cfg'

        entity = 'tests/samples/codefiles/see.h'

        args = ['--file', entity, '--config', config, '--time', now]

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['language'], language)

        entity = 'tests/samples/codefiles/seeplusplus.h'
        args[1] = entity

        retval = execute(args)
        self.assertEquals(retval, 102)

        language = u('C++')
        self.assertEqual(self.patched['wakatime.offlinequeue.Queue.push'].call_args[0][0]['language'], language)