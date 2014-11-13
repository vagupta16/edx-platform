from courseware.models import StudentModule
from courseware.models import GroupedQueries, GroupedQueriesStudents, GroupedQueriesSubqueries
from courseware.models import QueriesSaved, QueriesStudents, QueriesTemporary
from bulk_email.models import Optout
#todo: specific imports
from django.contrib.auth.models import User
from data_access_constants import *
from django.db.models import Q
from collections import defaultdict

def make_single_query(course_id, query):
    if query.type==QUERY_TYPE.SECTION:
        results = get_section_users_s(course_id, query, None)
    else:
        results = get_problem_users_s(course_id, query, None)

    #store query into QueriesTemporary
    q = QueriesTemporary(inclusion=INCLUSION_MAP.get(query.inclusion),
                         course_id = course_id,
                         module_state_key=query.id,
                         filter_on=query.filter)

    q.save()
    students = results.getResults()
    for student in students:
        row = QueriesStudents(query=q, inclusion=INCLUSION_MAP[query.inclusion], student=User.objects.filter(id=student[0])[0])
        row.save()

    return {q.id:results}

def make_total_query(course_id, existing_queries):
    results = QueryResults()
    querySpecific = set()
    if len(existing_queries) !=0:
        qs= make_existing(existing_queries)
        for row in qs:
            student = row.student
            #querySpecific.add((student.id, student.email))
            querySpecific.add((row.student_id, row.student.email))
        results.addCanInclude(querySpecific)

    return {0:results}



def get_problem_users_s(course_id, query, existing_queries):
    if query.filter==PROBLEM_FILTERS.OPENED:
        results = open_query(course_id, query, existing_queries)
    elif query.filter==PROBLEM_FILTERS.COMPLETED:
        results = completed_query(course_id, query, existing_queries)
    return results

def get_section_users_s(course_id, query, existing_queries):
    return open_query(course_id, query, existing_queries)


def make_existing(existing_queries):
    query = StudentModule.objects
    if existing_queries==None:
        return query

    queryDct = defaultdict(list)
    for q in existing_queries:
        if q=="" or q=="working":
            continue
        inclusionType = QueriesTemporary.objects.filter(id=q)
        result =  QueriesStudents.objects.filter(query_id=q)
        if inclusionType.exists():
            queryDct[inclusionType[0].inclusion].append(result)

    for notquery in queryDct[INCLUSION_MAP.get(INCLUSION.NOT)]:
        query = query.exclude(id__in=notquery)

    for andquery in queryDct[INCLUSION_MAP.get(INCLUSION.AND)]:
        andquery = andquery.values_list('student_id', flat=True)
        query = query.filter(student_id__in=andquery)


    orsQ = StudentModule.objects.none()
    for orQuery in queryDct[INCLUSION_MAP.get(INCLUSION_MAP.get(INCLUSION.OR))]:
        orsQ = orQuery | orsQ

    return query | orsQ


def completed_query(course_id, query, existing_queries):
    starting = make_existing(existing_queries)
    querySet = starting.filter(module_state_key=query.id, course_id = course_id).filter(~Q(grade=None))
    return processResults(course_id, query, querySet)


def open_query(course_id, query,  existing_queries):
    starting = make_existing(existing_queries)
    queryset = starting.filter(module_state_key=query.id, course_id = course_id)
    return processResults(course_id, query, queryset)

def filter_out_students(course_id,  queryset):
    return queryset.exclude(id__in = Optout.objects.all())
    """
    filterOut = Optout.objects.filter(course_id=course_id)
    filterout_ids = set([result.user.id for result in filterOut])
    return filterout_ids
    """


def processResults(course_id, query, queryset):
    filterout_ids = filter_out_students(course_id, queryset)

    results = QueryResults()
    querySpecific = set()
    #if query.filter==SECTION_FILTERS.OPENED:
    for row in queryset:
        if (row.student_id not in filterout_ids):
            querySpecific.add((row.student_id, row.student.email))

    if query.inclusion == INCLUSION.OR:
        results.addCanInclude(querySpecific)
    elif query.inclusion == INCLUSION.AND:
        results.addMustInclude(querySpecific)
    elif query.inclusion== INCLUSION.NOT:
        results.addDontInclude(querySpecific)
    return results



"""
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

def get_problem_users(course_id, queries, existing_queries):
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
"""