"""
Generate report of course forum data
"""


from datetime import date

from bson.son import SON
from django.conf import settings
from django_comment_client.management_utils import get_mongo_connection_string
from pymongo import MongoClient
from pymongo.errors import PyMongoError

FORUMS_MONGO_PARAMS = settings.FORUM_MONGO_PARAMS


def collect_course_forums_data(course_id):
    """
    Given a SlashSeparatedCourseKey course_id, return headers and information
    related to course forums usage such as upvotes, downvotes, and number of posts
    """
    try:
        client = MongoClient(get_mongo_connection_string())
        mongodb = client[FORUMS_MONGO_PARAMS['database']]
        new_threads_query = _generate_course_forums_query(course_id, "CommentThread")
        new_responses_query = _generate_course_forums_query(course_id, "Comment", False)
        new_comments_query = _generate_course_forums_query(course_id, "Comment", True)

        new_threads = mongodb.contents.aggregate(new_threads_query)['result']
        new_responses = mongodb.contents.aggregate(new_responses_query)['result']
        new_comments = mongodb.contents.aggregate(new_comments_query)['result']
    except PyMongoError:
        raise

    for entry in new_responses:
        entry['_id']['type'] = "Response"
    results = _merge_join_course_forums(new_threads, new_responses, new_comments)
    parsed_results = [
        [
            "{0}-{1}-{2}".format(result['_id']['year'], result['_id']['month'], result['_id']['day']),
            result['_id']['type'],
            result['posts'],
            result['up_votes'],
            result['down_votes'],
            result['net_points'],
        ]
        for result in results
    ]
    header = ['Date', 'Type', 'Number', 'Up Votes', 'Down Votes', 'Net Points']
    return header, parsed_results


def _generate_course_forums_query(course_id, query_type, parent_id_check=None):
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


def _merge_join_course_forums(threads, responses, comments):
    """
    Performs a merge of sorted threads, responses, comments data
    interleaving the results so the final result is in chronological order
    """
    data = []
    t_index, r_index, c_index = 0, 0, 0
    while (t_index < len(threads) or r_index < len(responses) or c_index < len(comments)):
        # checking out of bounds
        if t_index == len(threads):
            thread_date = date.max
        else:
            thread = threads[t_index]['_id']
            thread_date = date(thread["year"], thread["month"], thread["day"])
        if r_index == len(responses):
            response_date = date.max
        else:
            response = responses[r_index]["_id"]
            response_date = date(response["year"], response["month"], response["day"])
        if c_index == len(comments):
            comment_date = date.max
        else:
            comment = comments[c_index]["_id"]
            comment_date = date(comment["year"], comment["month"], comment["day"])

        if thread_date <= comment_date and thread_date <= response_date:
            data.append(threads[t_index])
            t_index += 1
            continue
        elif response_date <= thread_date and response_date <= comment_date:
            data.append(responses[r_index])
            r_index += 1
            continue
        else:
            data.append(comments[c_index])
            c_index += 1
    return data
