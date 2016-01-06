"""
Assert that the SchoolBus Backend transmits events properly
"""
from __future__ import absolute_import

from mock import patch, Mock
import logging

from django.test import TestCase
from south.utils import datetime_utils as datetime

from student.tests.factories import UserFactory
from track.backends.schoolbus import SchoolBusAnalyticsBackend


LOG = logging.getLogger(__name__)


class TestSchoolBusBackend(TestCase):
    """
    Assert that the SchoolBus Analytics Backend transmits events properly

    SchoolBus should only process event types in a pre-defined list.
    Course IDs must be part of the whitelisted set.
    Most event data like user_agent is arbitrary and can be changed.
    """
    def setUp(self):
        """
        Initialize SchoolBus Backend tests
        """
        course_ids = {
            'edX/DemoX/Demo_Course',
            'edX/DemoX/Demo_Course1',
        }
        events = [
            'hint_button',
            'problem_get',
            'problem_check',
            'problem_reset',
            'problem_save',
            'problem_show',
            'problem_start',
            'score_update',
            'input_ajax',
            'ungraded_response',
        ]
        self.backend = SchoolBusAnalyticsBackend(
            url='https://example.com/',
            path='path',
            key='key',
            secret='secret',
            course_ids=course_ids,
            events=events,
        )
        self.user = UserFactory.create()
        self.user.save()

    @patch('track.backends.schoolbus.urllib2.urlopen')
    def test_backend_correct_event_type(self, mock_urlopen):
        """
        Assert that problem_check events are sent
        """
        mock_response = Mock()
        mock_response.code = 200
        mock_urlopen.return_value = mock_response

        # pylint: disable=line-too-long
        event = {
            'username': 'verified',
            'event_type': 'problem_check',
            'ip': '10.0.2.2',
            'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.124 Safari/537.36',
            'host': 'precise64',
            'referer': 'https://example.com/courses/edX/DemoX/Demo_Course/courseware/interactive_demonstrations/basic_questions/',
            'accept_language': 'en-US;q=1.0, en;q=0.8',
            'event': {
                'submission': {
                    u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': {
                        'input_type': 'imageinput',
                        'question': '',
                        'response_type': 'imageresponse',
                        'answer': u'[480,237]',
                        'variant': '',
                        'correct': True,
                    },
                },
                'success': 'correct',
                'grade': 1,
                'correct_map': {
                    'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': {
                        'hint': '',
                        'hintmode': None,
                        'correctness': 'correct',
                        'npoints': None,
                        'answervariable': None,
                        'msg': '',
                        'queuestate': None,
                    },
                },
                'state': {
                    'student_answers': {
                        u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': u'[231,198]',
                    },
                    'seed': 1,
                    'done': True,
                    'correct_map': {
                        u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': {
                            'hint': u'',
                            'hintmode': None,
                            'correctness': u'incorrect',
                            'npoints': None,
                            'answervariable': None,
                            'msg': u'',
                            'queuestate': None,
                        },
                    },
                    'input_state': {
                        u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': {},
                    },
                },
                'answers': {
                    u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': u'[480,237]',
                },
                'attempts': 71,
                'max_grade': 1,
                'problem_id': u'i4x://edX/DemoX/problem/c554538a57664fac80783b99d9d6da7c',
            },
            'event_source': 'server',
            'context': {
                'course_user_tags': {},
                'user_id': self.user.pk,
                'org_id': 'edX',
                'module': {
                    'usage_key': u'i4x://edX/DemoX/problem/c554538a57664fac80783b99d9d6da7c',
                    'display_name': u'Pointing on a Picture',
                },
                'course_id': u'edX/DemoX/Demo_Course',
                'path': u'/courses/edX/DemoX/Demo_Course/xblock/i4x:;_;_edX;_DemoX;_problem;_c554538a57664fac80783b99d9d6da7c/handler/xmodule_handler/problem_check',
            },
            'time': datetime.datetime.now,
            'page': 'x_module',
        }
        # pylint: enable=line-too-long
        message = self.backend.send(event)
        self.assertEqual(message, 'OK')

    def test_backend_wrong_event_type(self):
        """
        Assert that events not in events list are not sent
        """
        # pylint: disable=line-too-long
        event = {
            'username': u'verified',
            'event_type': u'/courses/edX/DemoX/Demo_Course/courseware/interactive_demonstrations/',
            'ip': '10.0.2.2',
            'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.124 Safari/537.36',
            'host': 'precise64',
            'referer': 'https://example.com/courses/edX/DemoX/Demo_Course/info',
            'accept_language': 'en-US,en;q=0.8',
            'event': '{"POST": {}, "GET": {}}',
            'event_source': 'server',
            'context': {
                'course_user_tags': {},
                'user_id': self.user.pk,
                'org_id': 'edX',
                'course_id': u'edX/DemoX/Demo_Course',
                'path': u'/courses/edX/DemoX/Demo_Course/courseware/interactive_demonstrations/',
            },
            'time': datetime.datetime.now,
            'page': None,
        }
        # pylint: enable=line-too-long
        message = self.backend.send(event)
        self.assertIsNone(message)

    def test_backend_wrong_courseid(self):
        """
        Assert that non-whitelisted courses will not have their data sent
        """
        # pylint: disable=line-too-long
        event = {
            'username': 'verified',
            'event_type': 'problem_check',
            'ip': '10.0.2.2',
            'agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.124 Safari/537.36',
            'host': 'precise64',
            'referer': 'https://example.com/courses/edX/DemoX/Demo_Course/courseware/interactive_demonstrations/basic_questions/',
            'accept_language': 'en-US;q=1.0, en;q=0.8',
            'event': {
                'submission': {
                    u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': {
                        'input_type': 'imageinput',
                        'question': '',
                        'response_type': 'imageresponse',
                        'answer': u'[480,237]',
                        'variant': '',
                        'correct': True,
                    },
                },
                'success': 'correct',
                'grade': 1,
                'correct_map': {
                    'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': {
                        'hint': '',
                        'hintmode': None,
                        'correctness': 'correct',
                        'npoints': None,
                        'answervariable': None,
                        'msg': '',
                        'queuestate': None,
                    },
                },
                'state': {
                    'student_answers': {
                        u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': u'[231,198]',
                    },
                    'seed': 1,
                    'done': True,
                    'correct_map': {
                        u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': {
                            'hint': u'',
                            'hintmode': None,
                            'correctness': u'incorrect',
                            'npoints': None,
                            'answervariable': None,
                            'msg': u'',
                            'queuestate': None,
                        },
                    },
                    'input_state': {
                        u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': {},
                    },
                },
                'answers': {
                    u'i4x-edX-DemoX-problem-c554538a57664fac80783b99d9d6da7c_2_1': u'[480,237]',
                },
                'attempts': 71,
                'max_grade': 1,
                'problem_id': u'i4x://edX/DemoX/problem/c554538a57664fac80783b99d9d6da7c',
            },
            'event_source': 'server',
            'context': {
                'course_user_tags': {},
                'user_id': self.user.pk,
                'org_id': 'edX',
                'module': {
                    'usage_key': u'i4x://edX/DemoX/problem/c554538a57664fac80783b99d9d6da7c',
                    'display_name': u'Pointing on a Picture',
                },
                'course_id': u'edX/DemoX/Demo_Course2',
                'path': u'/courses/edX/DemoX/Demo_Course/xblock/i4x:;_;_edX;_DemoX;_problem;_c554538a57664fac80783b99d9d6da7c/handler/xmodule_handler/problem_check',
            },
            'time': datetime.datetime.now,
            'page': 'x_module',
        }
        # pylint: enable=line-too-long
        message = self.backend.send(event)
        self.assertIsNone(message)
