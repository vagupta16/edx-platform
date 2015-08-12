"""
Helpers for instructor dashboard > data download > forum reports
"""


from django.conf import settings
from django_comment_client.management_utils import get_mongo_connection_string
from pymongo import MongoClient
from pymongo.errors import PyMongoError

FORUMS_MONGO_PARAMS = settings.FORUM_MONGO_PARAMS


def collect_student_forums_data(course_id):
    """
    Given a SlashSeparatedCourseKey course_id, return headers and information
    related to student forums usage
    """
    try:
        client = MongoClient(get_mongo_connection_string())
        mongodb = client[FORUMS_MONGO_PARAMS['database']]
        student_forums_query = generate_student_forums_query(course_id)
        results = mongodb.contents.aggregate(student_forums_query)['result']
    except PyMongoError:
        raise

    parsed_results = [
        [
            result['_id'],
            result['posts'],
            result['votes'],
        ] for result in results
    ]
    header = ['Username', 'Posts', 'Votes']
    return header, parsed_results


def generate_student_forums_query(course_id):
    """
    generates an aggregate query for student data which can be executed using pymongo
    :param course_id:
    :return: a list with dictionaries to fetch aggregate query for
    student forums data
    """
    query = [
        {
            "$match": {
                "course_id": course_id.to_deprecated_string(),
            }
        },

        {
            "$group": {
                "_id": "$author_username",
                "posts": {"$sum": 1},
                "votes": {"$sum": "$votes.point"}
            }
        },
    ]
    return query
