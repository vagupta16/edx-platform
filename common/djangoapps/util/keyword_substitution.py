from django.contrib.auth.models import User

"""
keyword_substitution.py

Contains utility functions to help substitute keywords in a text body with
the appropriate user / course data.

Supported:
    %%USER_ID%% => anonymous user id
    %%USER_FULLNAME%% => User's full name
"""

KEYWORD_FUNCTION_MAP = {}

def setup_module(keyword_map):
    """
    Setup the keyword function map with the right class
    """
    KEYWORD_FUNCTION_MAP = keyword_map
    print "printing keyword_map"
    print keyword_map
    
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
    
    print "subbing"
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
