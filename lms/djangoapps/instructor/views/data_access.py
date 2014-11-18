from courseware.models import StudentModule
from courseware.models import GroupedQueries, GroupedQueriesStudents, GroupedQueriesSubqueries
from courseware.models import QueriesSaved, QueriesStudents, QueriesTemporary
from bulk_email.models import Optout
#todo: specific imports
from django.contrib.auth.models import User
from data_access_constants import *
from django.db.models import Q
from collections import defaultdict
import time


def saveQuery(course_id, queries):
    tempQueries = QueriesTemporary.objects.filter(id__in=queries)
    group = GroupedQueries(course_id = course_id, title = "")
    group.save()
    for tempQuery in tempQueries:
        permQuery = QueriesSaved(inclusion=tempQuery.inclusion,
                                 course_id=course_id,
                                 module_state_key=tempQuery.module_state_key,
                                 filter_on=tempQuery.filter_on,
                                 entity_name=tempQuery.entity_name)
        permQuery.save()
        relation = GroupedQueriesSubqueries(grouped=group,
                                            query=permQuery)
        relation.save()
    return True

def retrieveSavedQueries(course_id):
    group = GroupedQueries.objects.filter(course_id = course_id)
    relation = GroupedQueriesSubqueries.objects.filter(grouped__in=group)
    queries = QueriesSaved.objects.filter(id__in=relation.values_list('query'))

    if len(group)>0:
        return group[0].created, queries
    else:
        return 0, []





def make_single_query(course_id, query):
    #store query into QueriesTemporary
    q = QueriesTemporary(inclusion=INCLUSION_MAP.get(query.inclusion),
                         course_id = course_id,
                         module_state_key=query.id,
                         filter_on=query.filter,
                         entity_name=query.entityName)
    q.save()

    if query.type==QUERY_TYPE.SECTION:
        students = get_section_users_s(course_id, query)
    else:
        students = get_problem_users_s(course_id, query)

    for studentid, studentemail in students:
        row = QueriesStudents(query=q, inclusion=INCLUSION_MAP[query.inclusion], student=User.objects.filter(id=studentid)[0])
        row.save()

    return {q.id:students}

def make_total_query(course_id, existing_queries):
    querySpecific = set()
    if len(existing_queries) !=0:
        queryset= make_existing(existing_queries).values_list('student_id','student__email').distinct()
        for row in queryset:
            #querySpecific.add((student.id, student.email))
            querySpecific.add((row[0], row[1]))

    return {0:querySpecific}



def get_problem_users_s(course_id, query):
    if query.filter==PROBLEM_FILTERS.OPENED:
        results = open_query(course_id, query)
    elif query.filter==PROBLEM_FILTERS.COMPLETED:
        results = completed_query(course_id, query)
    return results

def get_section_users_s(course_id, query):
    return open_query(course_id, query)


def make_existing(existing_queries):
    query = StudentModule.objects
    if existing_queries==None:
        return query

    queryDct = defaultdict(list)
    for q in existing_queries:
        if q=="" or q=="working":
            continue
        inclusionType = QueriesTemporary.objects.filter(id=q)
        result =  QueriesStudents.objects.filter(query_id=q).values_list("student_id",flat=True)
        if inclusionType.exists():
            queryDct[inclusionType[0].inclusion].append(result)

    for notquery in queryDct[INCLUSION_MAP.get(INCLUSION.NOT)]:
        query = query.exclude(student_id__in=notquery)

    for andquery in queryDct[INCLUSION_MAP.get(INCLUSION.AND)]:
        query = query.filter(student_id__in=andquery)



    orQuery = StudentModule.objects
    qobjs = Q()
    for orq in queryDct[INCLUSION_MAP.get(INCLUSION.OR)]:
        qobjs = qobjs |(Q(student_id__in=orq))


    return query | orQuery.filter(qobjs)


def completed_query(course_id, query):
    #starting = make_existing(existing_queries)
    querySet = StudentModule.objects.filter(module_state_key=query.id, course_id = course_id).filter(~Q(grade=None))
    return processResults(course_id, query, querySet)


def open_query(course_id, query):
    #starting = make_existing(existing_queries)
    queryset = StudentModule.objects.filter(module_state_key=query.id, course_id = course_id)
    return processResults(course_id, query, queryset)

def filter_out_students(course_id,  queryset):
    return queryset.exclude(id__in = Optout.objects.all().values_list('user_id'))
    """
    filterOut = Optout.objects.filter(course_id=course_id)
    filterout_ids = set([result.user.id for result in filterOut])
    return filterout_ids
    """


def processResults(course_id, query, queryset):
    filteredQuery = filter_out_students(course_id, queryset)
    values = filteredQuery.values_list('student_id','student__email').distinct()
    return values



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