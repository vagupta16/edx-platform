"""
Helpers for instructor dashboard > data download > forum reports
"""


from bson.son import SON
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


def generate_course_forums_query(course_id, query_type, parent_id_check=None):
    """
    We can make one of 3 possible queries: CommentThread, Comment, or Response
    CommentThread is specified by _type
    Response, Comment are both _type="Comment". Comment differs in that it has a
    parent_id, so parent_id_check is set to True for Comments.
    """
    query = [
        {'$match': {
            'course_id': course_id.to_deprecated_string(),
            '_type': query_type,
        }},
        {'$project': {
            'year': {'$year': '$created_at'},
            'month': {'$month': '$created_at'},
            'day': {'$dayOfMonth': '$created_at'},
            'type': '$_type',
            'votes': '$votes',
        }},
        {'$group': {
            '_id': {
                'year': '$year',
                'month': '$month',
                'day': '$day',
                'type': '$type',
            },
            'posts': {"$sum": 1},
            'net_points': {'$sum': '$votes.point'},
            'up_votes': {'$sum': '$votes.up_count'},
            'down_votes': {'$sum': '$votes.down_count'},
        }},
        # order of the sort is important so we use SON
        {'$sort': SON([('_id.year', 1), ('_id.month', 1), ('_id.day', 1)])},
    ]
    if query_type == 'Comment':
        if parent_id_check is not None:
            query[0]['$match']['parent_id'] = {'$exists': parent_id_check}
    return query
