from courseware.models import StudentModule
from data_access_constants import *

def get_users(course_id, queries):
    splitted = {QUERY_TYPE.SECTION:[],
                QUERY_TYPE.PROBLEM:[]
    }
    #if there is at least one or, then we merge. otherwise we intersect
    sectionOr = False
    problemOr = False

    for query in queries:
        if query.type==QUERY_TYPE.SECTION:
            splitted[QUERY_TYPE.SECTION].append(query)
        else:
            splitted[QUERY_TYPE.PROBLEM].append(query)
    sectionResults = get_section_users(course_id, splitted[QUERY_TYPE.SECTION])
    unifiedResults = get_section_users(course_id, splitted[QUERY_TYPE.SECTION], sectionResults)
    #for each thing's .student.email  .student.id
    return unifiedResults



def get_section_users(course_id, queries, resultset = None):
    currentSet = set()

    return "hai"


def get_problem_users(course_id, queries, resultset = None):

    return "hai"