from courseware.models import StudentModule
from courseware.models import GroupedQueries, GroupedQueriesSubqueries, GroupedTempQueriesSubqueries
from courseware.models import QueriesSaved, QueriesStudents, QueriesTemporary
from bulk_email.models import Optout
from student.models import UserProfile
from student.models import CourseEnrollment
from django.contrib.auth.models import User
from data_access_constants import INCLUSION_MAP,QUERY_TYPE, PROBLEM_FILTERS, SECTION_FILTERS, INCLUSION, QUERYSTATUS, REVERSE_INCLUSION_MAP, Query
from data_access_constants import DATABASE_FIELDS
from django.db.models import Q
from collections import defaultdict
import random
import datetime
from celery import task
import time

def deleteSavedQuery(queryToDelete):
    groupedQ = GroupedQueries.objects.filter(id=queryToDelete)
    subqueriesToDelete = GroupedQueriesSubqueries.objects.filter(grouped_id=queryToDelete)
    queriesSaved = QueriesSaved.objects.filter(id__in=subqueriesToDelete.values_list(DATABASE_FIELDS.QUERY_ID))
    #Needs to be in this specific order for deletion
    queriesSaved.delete()
    subqueriesToDelete.delete()
    groupedQ.delete()

def deleteTemporaryQuery(queryToDelete):
    tempQuery = QueriesTemporary.objects.filter(id=queryToDelete)
    savedStudents = QueriesStudents.objects.filter(query_id=queryToDelete)
    savedStudents.delete()
    tempQuery.delete()

def deleteBulkTemporaryQuery(queryToDelete):
    querySet = set()
    for query in queryToDelete:
        querySet.add(query)
    print queryToDelete
    tempQuery = QueriesTemporary.objects.filter(id__in=querySet)
    savedStudents = QueriesStudents.objects.filter(query_id__in=querySet)
    savedStudents.delete()
    tempQuery.delete()

def saveQuery(course_id, queries):
    tempQueries = QueriesTemporary.objects.filter(id__in=queries)
    group = GroupedQueries(course_id = course_id, title = "")
    group.save()
    for tempQuery in tempQueries:
        permQuery = QueriesSaved(inclusion=tempQuery.inclusion,
                                 course_id=course_id,
                                 module_state_key=tempQuery.module_state_key,
                                 filter_on=tempQuery.filter_on,
                                 entity_name=tempQuery.entity_name,
                                 type=tempQuery.type)
        permQuery.save()
        relation = GroupedQueriesSubqueries(grouped=group,
                                            query=permQuery)
        relation.save()
    return True

#Asynchronously makes the subqueries for a group and then aggregates them once the subqueries are finished.
@task
def getGroupQueryStudents(course_id, groupId):
    group, queries, relation = retrieveSavedQueries(course_id, groupId)
    chainedStudents = (makeSubqueries.si(course_id, groupId, queries) | retrieveGroupedQuery.si(course_id, groupId))().get()
    return chainedStudents

@task  # pylint: disable=E1102
def retrieveGroupedQuery(course_id, groupId):
     subqueries = GroupedTempQueriesSubqueries.objects.filter(grouped_id=groupId).distinct()
     existing = []
     for sub in subqueries:
         existing.append(sub.query_id)
     studentInfo = make_existing_query(existing).\
        values_list(DATABASE_FIELDS.ID,
                    DATABASE_FIELDS.EMAIL,
                    DATABASE_FIELDS.PROFILE_NAME).distinct()
     students = [{"id":pair[0],"email":pair[1],"profileName":pair[2]} for pair in students]
     subqueries.delete()
     return students


@task  # pylint: disable=E1102
def makeSubqueries(course_id,groupid,  queries):
    for query in queries:
        query = Query(query.type,
                      REVERSE_INCLUSION_MAP[query.inclusion],
                      '/'.join([query.module_state_key.block_type, query.module_state_key.block_id]),
                      query.filter_on,
                      query.entity_name)
        make_single_query.apply_async(args=(course_id, query, groupid))



def retrieveSavedQueries(course_id, specificGroup=None):
    if specificGroup:
        group = GroupedQueries.objects.filter(course_id = course_id, id=specificGroup)
    else:
        group = GroupedQueries.objects.filter(course_id = course_id)
    relation = GroupedQueriesSubqueries.objects.filter(grouped__in=group)
    queries = QueriesSaved.objects.filter(id__in=relation.values_list(DATABASE_FIELDS.QUERY))
    if len(group)>0:
        return (group, queries, relation)
    else:
        return ([], [], [])

def retrieveTempQueries(course_id):
    queriesTemp = QueriesTemporary.objects.filter(course_id = course_id)
    return queriesTemp


@task  # pylint: disable=E1102
def make_single_query(course_id, query, associateGroup=None):
    q = QueriesTemporary(inclusion=INCLUSION_MAP.get(query.inclusion),
                         course_id = course_id,
                         module_state_key=query.entityId,
                         filter_on=query.filter,
                         entity_name=query.entityName,
                         type=query.type,
                         done=False)
    q.save()
    try:
        if query.type==QUERY_TYPE.SECTION:
            students = get_section_users(course_id, query)
        else:
            students = get_problem_users(course_id, query)
        for studentid, studentemail in students:
            row = QueriesStudents(query=q, inclusion=INCLUSION_MAP[query.inclusion], student=User.objects.filter(id=studentid)[0])
            row.save()
        QueriesTemporary.objects.filter(id=q.id).update(done=True)
        if associateGroup !=None:
            g = GroupedTempQueriesSubqueries(grouped_id=associateGroup, query_id=q.id)
            g.save()

    except Exception as e:
        QueriesTemporary.objects.filter(id=q.id).update(done=None)
        raise(e)

    #on every 10th query, purge the temporary queries
    rand = random.random()
    if rand>.9:
        purgeTemporaryQueries()
    return {q.id:students}

def purgeTemporaryQueries():
    """
    Delete queries made more than 30 minutes ago along with the saved students from those queries
    """
    minutes30ago = datetime.datetime.now()-datetime.timedelta(minutes=30)
    oldQueries = QueriesTemporary.objects.filter(created__lt=minutes30ago)
    savedStudents = QueriesStudents.objects.filter(query_id__in=oldQueries.values_list(DATABASE_FIELDS.ID))
    savedStudents.delete()
    oldQueries.delete()

@task  # pylint: disable=E1102
def make_total_query(existing_queries):
    aggregateExisting = set()
    if len(existing_queries) !=0:
        queryset= make_existing_query(existing_queries).values_list(DATABASE_FIELDS.ID,
                                                                    DATABASE_FIELDS.EMAIL,
                                                                    DATABASE_FIELDS.PROFILE_NAME).distinct()
        for row in queryset:
            aggregateExisting.add((row[0], row[1], row[2]))
    return aggregateExisting

def get_problem_users(course_id, query):
    """
    Gets Students filtered on specified problem-specific query criteria
    """
    if query.filter==PROBLEM_FILTERS.OPENED:
        results = open_query(course_id, query)
    elif query.filter==PROBLEM_FILTERS.COMPLETED:
        results = completed_query(course_id, query)
    elif query.filter==PROBLEM_FILTERS.NOT_OPENED:
        results = not_open_query(course_id, query)
    elif query.filter==PROBLEM_FILTERS.NOT_COMPLETED:
        results = not_completed_query(course_id, query)
    return results

def get_section_users(course_id, query):
    """
    Gets Students filtered on specified section-specific query criteria
    """
    if query.filter == SECTION_FILTERS.OPENED:
        results =  open_query(course_id, query)
    elif query.filter == SECTION_FILTERS.NOT_OPENED:
        results = not_open_query(course_id, query)
    return results

def make_existing_query(existing_queries):
    """
    Aggregates single queries in a group into one unified set of students
    """
    query = User.objects
    if existing_queries==None:
        return query
    queryDct = defaultdict(list)
    for q in existing_queries:
        if q=="" or q==QUERYSTATUS.WORKING:
            continue
        inclusionType = QueriesTemporary.objects.filter(id=q)
        result =  QueriesStudents.objects.filter(query_id=q).values_list(DATABASE_FIELDS.STUDENT_ID,flat=True)
        if inclusionType.exists():
            queryDct[inclusionType[0].inclusion].append(result)

    for notquery in queryDct[INCLUSION_MAP.get(INCLUSION.NOT)]:
        query = query.exclude(id__in=notquery)

    for andquery in queryDct[INCLUSION_MAP.get(INCLUSION.AND)]:
        query = query.filter(id__in=andquery)

    orQuery = User.objects
    qobjs = Q()
    for orq in queryDct[INCLUSION_MAP.get(INCLUSION.OR)]:
        qobjs = qobjs |(Q(id__in=orq))
    if len(queryDct[INCLUSION_MAP.get(INCLUSION.NOT)])==0 and len(queryDct[INCLUSION_MAP.get(INCLUSION.AND)])==0:
        return orQuery.filter(qobjs)
    else:
        return query | orQuery.filter(qobjs)



def not_open_query(course_id, query):
    """
    Specific db query for sections or problems that have not been opened
    """
    idsInCourse = CourseEnrollment.objects.filter(course_id=course_id, is_active=1).values_list(DATABASE_FIELDS.USER_ID)
    totalStudents = User.objects.filter(id__in=idsInCourse)
    withoutOpen = totalStudents.exclude(id__in=StudentModule.objects.filter(module_state_key=query.entityId,
                                                                            course_id = course_id).
                                                                            values_list(DATABASE_FIELDS.STUDENT_ID))
    return processResults(course_id, withoutOpen, DATABASE_FIELDS.ID, DATABASE_FIELDS.EMAIL)

def not_completed_query(course_id, query):
    """
    Specific db query for sections or problems that are not completed
    """
    idsInCourse = CourseEnrollment.objects.filter(course_id=course_id, is_active=1).values_list(DATABASE_FIELDS.USER_ID)
    totalStudents = User.objects.filter(id__in=idsInCourse)

    withoutCompleted = totalStudents.exclude(id__in= StudentModule.objects.filter(module_state_key=query.entityId,
                                                                                  course_id = course_id).
                                                                                  filter(~Q(grade=None)).
                                                                                  values_list(DATABASE_FIELDS.STUDENT_ID))
    return processResults(course_id, query, withoutCompleted, DATABASE_FIELDS.ID, DATABASE_FIELDS.EMAIL)

def completed_query(course_id, query):
    """
    Specific db query for sections or problems that are completed
    """
    querySet = StudentModule.objects.filter(module_state_key=query.entityId, course_id = course_id).filter(~Q(grade=None))
    return processResults(course_id, querySet, DATABASE_FIELDS.STUDENT_ID,DATABASE_FIELDS.STUDENT_EMAIL)

def open_query(course_id, query):
    """
    Specific db query for sections or problems that are opened
    """
    queryset = StudentModule.objects.filter(module_state_key=query.entityId, course_id = course_id)
    return processResults(course_id, queryset, DATABASE_FIELDS.STUDENT_ID,DATABASE_FIELDS.STUDENT_EMAIL)

def processResults(course_id, queryset, id_field , email_field):
    """
    Handles any intermediate filtering between specific query criteria and returning to the user
    """
    filteredQuery = filter_out_students_negative(course_id, queryset)
    values = filteredQuery.values_list(id_field, email_field).distinct()
    return values

def filter_out_students_negative(course_id,  queryset):
    """
    Exclude students who have opted out of emails and exclude students who are not active in the class
    Used specifically for positive queries i.e. have completed/opened because of query structure
    """
    withoutOptOut = queryset.exclude(id__in = Optout.objects.all().values_list(DATABASE_FIELDS.USER_ID))
    withoutNotEnrolled = withoutOptOut.exclude(id__in=
                              CourseEnrollment.objects.filter(course_id=course_id, is_active=0).
                              values_list(DATABASE_FIELDS.USER_ID))
    return withoutNotEnrolled

def filter_out_students_positive(course_id,  queryset):
    """
    Exclude students who have opted out of emails and exclude students who are not active in the class
    Used specifically for negative queries i.e. not completed/not opened because of query structure
    """
    withoutOptOut = queryset.exclude(student_id__in = Optout.objects.all().values_list(DATABASE_FIELDS.USER_ID))
    withoutNotEnrolled = withoutOptOut.exclude(student_id__in=
                              CourseEnrollment.objects.filter(course_id=course_id, is_active=0).
                              values_list(DATABASE_FIELDS.USER_ID))
    return withoutNotEnrolled


