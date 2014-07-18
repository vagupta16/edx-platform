from itertools import ifilter

from django.contrib.auth.models import User

from student.models import anonymous_id_for_user

"""
keyword_substitution.py

Contains utility functions to help substitute keywords in a text body with
the appropriate user / course data.

Supported:
    %%USER_ID%% => anonymous user id
    %%USER_FULLNAME%% => User's full name
"""


def get_anonymous_id_for_user(user, course_id):
    # Wrapper for anonymous_id_for_user
    return anonymous_id_for_user(user, course_id)


def get_user_name(user, course_id=None):
    # Wrapper for user.profile.name
    return user.profile.name

"""
Add any keywords that you wish to substitute here:
"""
KEYWORD_FUNCTION_MAP = {
    '%%USER_ID%%': get_anonymous_id_for_user,
    '%%USER_FULLNAME%%': get_user_name,
}


def substitute_keywords_with_data(string, user_id=None, course_id=None):
    """
    Iterates through all keywords that must be substituted and replaces
    them by calling the corresponding functions stored in KEYWORD_FUNCTION_MAP.

    Function stored in KEYWORD_FUNCTION_MAP must return a string to replace with.
    Also, functions imported from other modules must be wrapped around in a
    new function if they don't take in user_id and course_id. This is to simplify
    the forloop below, and eliminate the possibility of unnecessarily piling up
    if elif else statements when keyword pool grows.
    """

    # Do not proceed without parameters: Compatibility check with existing tests
    # That do not supply these parameters
    if user_id is None or course_id is None:
        return string

    # Memoize user objects
    user = User.objects.get(id=user_id)

    for key, func in KEYWORD_FUNCTION_MAP.iteritems():
        if key in string:
            substitutor = func(user, course_id)
            string = string.replace(key, substitutor)

    return string
