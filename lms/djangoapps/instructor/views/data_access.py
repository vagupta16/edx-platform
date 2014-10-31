from courseware.models import StudentModule
#todo: specific imports
from data_access_constants import *
from django.db.models import Q

def get_users(course_id, queries):
    splitted = {QUERY_TYPE.SECTION:[],
                QUERY_TYPE.PROBLEM:[]
    }

    for query in queries:
        if query.type==QUERY_TYPE.SECTION:
            splitted[QUERY_TYPE.SECTION].append(query)
        else:
            splitted[QUERY_TYPE.PROBLEM].append(query)

    sectionResults = get_section_users(course_id, splitted[QUERY_TYPE.SECTION])
    problemResults = get_problem_users(course_id, splitted[QUERY_TYPE.PROBLEM])

    #merge
    sectionResults.mergeIn(problemResults)
    return sectionResults.getResults()



def get_section_users(course_id, queries):
    results = QueryResults()
    for query in queries:
        querySpecific = set()
        #query for people that have interacted with the section
        qresults = open_query(query)
        results.mergeIn(qresults)
    return results


def get_problem_users(course_id, queries):
    results = QueryResults()
    for query in queries:
        querySpecific = set()
        #query for people that have interacted with the section
        qresults = open_query(query)
        results.mergeIn(qresults)
    return results


def open_query(query):
    results = QueryResults()
    querySpecific = set()
    queryset = StudentModule.objects.filter(module_state_key=query.id)
    if query.filter==SECTION_FILTERS.OPENED:
        for row in queryset:
            student = row.student
            querySpecific.add((student.id, student.email))
    if query.inclusion == INCLUSION.OR:
        results.addCanInclude(querySpecific)
    elif query.inclusion == INCLUSION.AND:
        results.addMustInclude(querySpecific)
    elif query.inclusion== INCLUSION.NOT:
        results.addDontInclude(querySpecific)
    return results
