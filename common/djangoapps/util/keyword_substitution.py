"""
keyword_substitution.py

Contains utility functions to help substitute keywords in a text body with
the appropriate user / course data.

Supported:
<<<<<<< HEAD
    LMS and CMS (email on enrollment):
        - %%USER_ID%% => anonymous user id
        - %%USER_FULLNAME%% => User's full name
        - %%COURSE_DISPLAY_NAME%% => display name of the course
        - %%COURSE_ID%% => course identifier
        - %%COURSE_START_DATE%% => start date of the course
=======
    LMS:
        - %%USER_ID%% => anonymous user id
        - %%USER_FULLNAME%% => User's full name
        - %%COURSE_DISPLAY_NAME%% => display name of the course
>>>>>>> 00b75f0119b981641833240be214ef2076329747
        - %%COURSE_END_DATE%% => end date of the course

Usage:
    KEYWORD_FUNCTION_MAP must be supplied in startup.py, so that it lives
    above other modules in the dependency tree and acts like a global var.
    Then we can call substitute_keywords_with_data where substitution is
    needed. Currently called in:
<<<<<<< HEAD
        - LMS:
            - Bulk email
            - emails on enrollment
            - course announcements
            - HTML components
        - CMS:
            - Test emails on enrollment
"""

from collections import namedtuple

from django.contrib.auth.models import User
from xmodule.modulestore.django import modulestore

Keyword = namedtuple('Keyword', 'func desc')
KEYWORD_FUNCTION_MAP = {}


def keyword_function_map_is_empty():
    """
    Checks if the keyword function map has been filled
    """
    return not bool(KEYWORD_FUNCTION_MAP)


def add_keyword_function_map(mapping):
    """
    Attaches the given keyword-function mapping to the existing one
    """
    KEYWORD_FUNCTION_MAP.update(mapping)


def get_keywords_supported():
    """
    Returns supported keywords as a list of dicts with name and description
    """
    return [
        {
            'name': keyword,
            'desc': value.desc,
        }
        for keyword, value in KEYWORD_FUNCTION_MAP.iteritems()
    ]


def substitute_keywords(string, user=None, course=None):
=======
        - LMS: Announcements + Bulk emails
        - CMS: Not called
"""

from django.contrib.auth.models import User
from student.models import anonymous_id_for_user
from xmodule.modulestore.django import modulestore


def anonymous_id_from_user_id(user_id):
    """
    Gets a user's anonymous id from their user id
    """
    user = User.objects.get(id=user_id)
    return anonymous_id_for_user(user, None)


def substitute_keywords(string, user_id, context):
>>>>>>> 00b75f0119b981641833240be214ef2076329747
    """
    Replaces all %%-encoded words using KEYWORD_FUNCTION_MAP mapping functions

    Iterates through all keywords that must be substituted and replaces
    them by calling the corresponding functions stored in KEYWORD_FUNCTION_MAP.

    Functions stored in KEYWORD_FUNCTION_MAP must return a replacement string.
<<<<<<< HEAD
    Also, functions imported from other modules must be wrapped in a
    new function if they don't take in user_id and course_id. This simplifies
    the loop below, and reduces the need for piling up if elif else statements
    when the keyword pool grows.
    """
    if user is None or course is None:
        # Cannot proceed without course and user information
        return string

    for key, value in KEYWORD_FUNCTION_MAP.iteritems():
        if key in string:
            substitutor = value.func(user, course)
            string = string.replace(key, substitutor)
=======
    """

    # do this lazily to avoid unneeded database hits
    KEYWORD_FUNCTION_MAP = {
        '%%USER_ID%%': lambda: anonymous_id_from_user_id(user_id),
        '%%USER_FULLNAME%%': lambda: context.get('name'),
        '%%COURSE_DISPLAY_NAME%%': lambda: context.get('course_title'),
        '%%COURSE_END_DATE%%': lambda: context.get('course_end_date'),
    }

    for key in KEYWORD_FUNCTION_MAP.keys():
        if key in string:
            substitutor = KEYWORD_FUNCTION_MAP[key]
            string = string.replace(key, substitutor())
>>>>>>> 00b75f0119b981641833240be214ef2076329747

    return string


<<<<<<< HEAD
def substitute_keywords_with_data(string, user_id=None, course_id=None):
    """
    Given user and course ids, replaces all %%-encoded words in the given string
=======
def substitute_keywords_with_data(string, context):
    """
    Given an email context, replaces all %%-encoded words in the given string
    `context` is a dictionary that should include `user_id` and `course_title`
    keys
>>>>>>> 00b75f0119b981641833240be214ef2076329747
    """

    # Do not proceed without parameters: Compatibility check with existing tests
    # that do not supply these parameters
<<<<<<< HEAD
    if user_id is None or course_id is None:
        return string

    # Grab user objects
    user = User.objects.get(id=user_id)
    course = modulestore().get_course(course_id, depth=0)

    return substitute_keywords(string, user, course)
=======
    user_id = context.get('user_id')
    course_title = context.get('course_title')

    if user_id is None or course_title is None:
        return string

    return substitute_keywords(string, user_id, context)
>>>>>>> 00b75f0119b981641833240be214ef2076329747
