from courseware.models import StudentModule
from courseware.models import GroupedQueries, GroupedQueriesStudents, GroupedQueriesSubqueries
from courseware.models import QueriesSaved, QueriesStudents, QueriesTemporary
from bulk_email.models import Optout
#todo: specific imports
from data_access_constants import *
from django.db.models import Q



def make_query(course_id, query):
    print query
    if query.type==QUERY_TYPE.SECTION:
        results = open_query(course_id, query)
    else:
        results = get_problem_users_s(course_id, query)

    #store query into QueriesTemporary
    q = QueriesTemporary(inclusion=INCLUSION_MAP.get(query.inclusion),
                         course_id = course_id,
                         module_state_key=query.id,
                         filter_on=query.filter)

    q.save()

    #store students into QueriesStudents



    #merge
    return {q.id:results}

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
        qresults = open_query(course_id, query)
        results.mergeIn(qresults)
    return results

def get_problem_users_s(course_id, query):
    if query.filter==PROBLEM_FILTERS.OPENED:
        results = open_query(course_id, query)
    elif query.filter==PROBLEM_FILTERS.COMPLETED:
        results = completed_query(course_id, query)
    return results

def get_section_users_s(course_id, query):
    return open_query(course_id, query)


def get_problem_users(course_id, queries):
    results = QueryResults()
    for query in queries:
        qresults = None
        querySpecific = set()
        #query for people that have interacted with the section
        if query.filter==PROBLEM_FILTERS.OPENED:
            qresults = open_query(course_id, query)
        elif query.filter==PROBLEM_FILTERS.COMPLETED:
            qresults = completed_query(course_id, query)
        if qresults:
            results.mergeIn(qresults)
    return results

def completed_query(course_id, query):
    queryset = StudentModule.objects.filter(module_state_key=query.id, course_id = course_id).filter(~Q(grade=None))
    print queryset.query
    return processResults(course_id, query, queryset)


def open_query(course_id, query):
    queryset = StudentModule.objects.filter(module_state_key=query.id, course_id = course_id)
    return processResults(course_id, query, queryset)

def filter_out_students(course_id):
    filterOut = Optout.objects.filter(course_id=course_id)
    filterout_ids = set([result.user.id for result in filterOut])
    return filterout_ids



def processResults(course_id, query, queryset):
    filterout_ids = filter_out_students(course_id)

    results = QueryResults()
    querySpecific = set()
    #if query.filter==SECTION_FILTERS.OPENED:
    for row in queryset:
        student = row.student
        if (student.id not in filterout_ids):
            querySpecific.add((student.id, student.email))

    if query.inclusion == INCLUSION.OR:
        results.addCanInclude(querySpecific)
    elif query.inclusion == INCLUSION.AND:
        results.addMustInclude(querySpecific)
    elif query.inclusion== INCLUSION.NOT:
        results.addDontInclude(querySpecific)
    return results