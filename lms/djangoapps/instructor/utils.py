"""
Helpers for instructor app.
"""


from xmodule.modulestore.django import modulestore

from courseware.model_data import FieldDataCache
from courseware.module_render import get_module


class DummyRequest(object):
    """Dummy request"""

    META = {}

    def __init__(self):
        self.session = {}
        self.user = None
        return

    def get_host(self):
        """Return a default host."""
        return 'edx.mit.edu'

    def is_secure(self):
        """Always insecure."""
        return False


def get_module_for_student(student, usage_key, request=None):
    """Return the module for the (student, location) using a DummyRequest."""
    if request is None:
        request = DummyRequest()
        request.user = student

    descriptor = modulestore().get_item(usage_key, depth=0)
    field_data_cache = FieldDataCache([descriptor], usage_key.course_key, student)
    return get_module(student, request, usage_key, field_data_cache)


from openedx.contrib.stanford.data_downloads.instructor_reports.data_forums import collect_course_forums_data
from openedx.contrib.stanford.data_downloads.instructor_reports.data_forums import merge_join_course_forums
from openedx.contrib.stanford.data_downloads.instructor_reports.data_forums import generate_course_forums_query
from openedx.contrib.stanford.data_ora2 import collect_anonymous_ora2_data
from openedx.contrib.stanford.data_ora2 import collect_email_ora2_data
from openedx.contrib.stanford.data_ora2 import collect_ora2_data
from openedx.contrib.stanford.data_ora2 import ora2_data_queries
from openedx.contrib.stanford.data_downloads.instructor_reports.data_forums import collect_student_forums_data
from openedx.contrib.stanford.data_downloads.instructor_reports.data_forums import generate_student_forums_query
