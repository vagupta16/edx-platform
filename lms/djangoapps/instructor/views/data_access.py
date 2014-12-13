"""
Methods associated with accessing models related to email list widget on instructor dashboard
"""
from courseware.models import StudentModule
from courseware.models import GroupedQueries, GroupedQueriesSubqueries, GroupedTempQueriesSubqueries
from courseware.models import QueriesSaved, QueriesStudents, QueriesTemporary
from bulk_email.models import Optout
from student.models import CourseEnrollment
from django.contrib.auth.models import User
from instructor.views.data_access_constants import INCLUSION_MAP, QUERY_TYPE, PROBLEM_FILTERS, SECTION_FILTERS
from instructor.views.data_access_constants import INCLUSION, QUERYSTATUS
from instructor.views.data_access_constants import REVERSE_INCLUSION_MAP, Query
from instructor.views.data_access_constants import DATABASE_FIELDS
from django.db.models import Q
from collections import defaultdict
import random
import datetime
from celery import task


def delete_saved_query(query_to_delete):
    """
    Deletes a specified grouped query along with its saved queries
    """
    grouped_query = GroupedQueries.objects.filter(id=query_to_delete)
    subqueries_to_delete = GroupedQueriesSubqueries.objects.filter(grouped_id=query_to_delete)
    queries_saved = QueriesSaved.objects.filter(id__in=subqueries_to_delete.values_list(DATABASE_FIELDS.QUERY_ID))
    #Needs to be in this specific order for deletion
    queries_saved.delete()
    subqueries_to_delete.delete()
    grouped_query.delete()


def delete_temporary_query(query_to_delete):
    """
    Removes a single query from the temporary queries
    """
    temp_query = QueriesTemporary.objects.filter(id=query_to_delete)
    saved_students = QueriesStudents.objects.filter(query_id=query_to_delete)
    saved_students.delete()
    temp_query.delete()


def delete_bulk_temporary_query(query_to_delete):
    """
    Removes many queries from the temporary query table
    """
    query_set = set()
    for query in query_to_delete:
        query_set.add(query)
    temp_query = QueriesTemporary.objects.filter(id__in=query_set)
    for query in temp_query:
        print query
    saved_students = QueriesStudents.objects.filter(query_id__in=query_set)
    saved_students.delete()
    temp_query.delete()


def save_query(course_id, queries):
    """
    Makes a new grouped query by saving the individual subqueries and then associating them to a grouped query
    """
    temp_queries = QueriesTemporary.objects.filter(id__in=queries)
    group = GroupedQueries(course_id=course_id, title="")
    group.save()
    for temp_query in temp_queries:
        perm_query = QueriesSaved(inclusion=temp_query.inclusion,
            course_id=course_id,
            module_state_key=temp_query.module_state_key,
            filter_on=temp_query.filter_on,
            entity_name=temp_query.entity_name,
            type=temp_query.type)
        perm_query.save()
        relation = GroupedQueriesSubqueries(grouped=group,
                                            query=perm_query)
        relation.save()
    return True


@task
def get_group_query_students(course_id, group_id):
    """
    Asynchronously makes the subqueries for a group and then aggregates them once the subqueries are finished.
    """
    _group, queries, _relation = get_saved_queries(course_id, group_id)
    chained_students = (make_subqueries.si(course_id, group_id, queries) |
        retrieve_grouped_query.si(course_id, group_id))().get()
    return chained_students


@task  # pylint: disable=E1102
def retrieve_grouped_query(_course_id, group_id):
    """
    For a grouped query where its subqueries have already been executed, return the students associated
    """
    subqueries = GroupedTempQueriesSubqueries.objects.filter(grouped_id=group_id).distinct()
    existing = []
    for sub in subqueries:
        existing.append(sub.query_id)
        student_info = make_existing_query(existing).\
            values_list(DATABASE_FIELDS.ID,
                DATABASE_FIELDS.EMAIL,
                DATABASE_FIELDS.PROFILE_NAME).distinct()
    students = [{"id": triple[0], "email": triple[1], "profileName": triple[2]} for triple in student_info]
    subqueries.delete()
    return students


@task  # pylint: disable=E1102
def make_subqueries(course_id, group_id, queries):
    """
    Issues the subqueries associated with a group query
    """
    for query in queries:
        query = Query(query.type,
            REVERSE_INCLUSION_MAP[query.inclusion],
            '/'.join([query.module_state_key.block_type, query.module_state_key.block_id]),
            query.filter_on,
            query.entity_name)
        make_single_query.apply_async(args=(course_id, query, group_id))


def get_saved_queries(course_id, specific_group=None):
    """
    Get existing saved queries associated with a given course
    """
    if specific_group:
        group = GroupedQueries.objects.filter(course_id=course_id, id=specific_group)
    else:
        group = GroupedQueries.objects.filter(course_id=course_id)
    relation = GroupedQueriesSubqueries.objects.filter(grouped__in=group)
    queries = QueriesSaved.objects.filter(id__in=relation.values_list(DATABASE_FIELDS.QUERY))
    if len(group) > 0:
        return (group, queries, relation)
    else:
        return ([], [], [])


def get_temp_queries(course_id):
    """
    Get temporary queries associated with a course
    """
    queries_temp = QueriesTemporary.objects.filter(course_id=course_id)
    return queries_temp


@task  # pylint: disable=E1102
def make_single_query(course_id, query, associate_group=None):
    """
    Make a single query for student information
    """
    temp_query = QueriesTemporary(inclusion=INCLUSION_MAP.get(query.inclusion),
        course_id=course_id,
        module_state_key=query.entity_id,
        filter_on=query.filter,
        entity_name=query.entity_name,
        type=query.type,
        done=False)
    temp_query.save()
    try:
        if query.type == QUERY_TYPE.SECTION:
            students = get_section_users(course_id, query)
        else:
            students = get_problem_users(course_id, query)

        bulk_queries = []
        for student_id, student_email in students:  # pylint: disable=unused-variable
            row = QueriesStudents(query=temp_query, inclusion=INCLUSION_MAP[query.inclusion], student=User.objects.filter(id=student_id)[0])
            bulk_queries.append(row)
        QueriesStudents.objects.bulk_create(bulk_queries)
        QueriesTemporary.objects.filter(id=temp_query.id).update(done=True)  # pylint: disable=no-member
        if associate_group is not None:
            grouped_temp = GroupedTempQueriesSubqueries(grouped_id=associate_group,
                query_id=temp_query.id)  # pylint: disable=no-member
            grouped_temp.save()

    except Exception as ex:
        QueriesTemporary.objects.filter(id=temp_query.id).update(done=None)  # pylint: disable=no-member
        raise(ex)

    #on every 10th query, purge the temporary queries
    rand = random.random()
    if rand > .9:
        purge_temporary_queries()
    return {temp_query.id: students}  # pylint: disable=no-member


def purge_temporary_queries():
    """
    Delete queries made more than 30 minutes ago along with the saved students from those queries
    """
    minutes30ago = datetime.datetime.now() - datetime.timedelta(minutes=30)
    old_queries = QueriesTemporary.objects.filter(created__lt=minutes30ago)
    saved_students = QueriesStudents.objects.filter(query_id__in=old_queries.values_list(DATABASE_FIELDS.ID))
    saved_students.delete()
    old_queries.delete()


@task  # pylint: disable=E1102
def make_total_query(existing_queries):
    """
    Given individual queries that have already been made , aggregate students associated with those queries
    """
    aggregate_existing = set()
    if len(existing_queries) != 0:
        queryset = make_existing_query(existing_queries).values_list(DATABASE_FIELDS.ID,
            DATABASE_FIELDS.EMAIL,
            DATABASE_FIELDS.PROFILE_NAME).distinct()
        for row in queryset:
            aggregate_existing.add((row[0], row[1], row[2]))
    return aggregate_existing


def get_problem_users(course_id, query):
    """
    Gets Students filtered on specified problem-specific query criteria
    """
    if query.filter == PROBLEM_FILTERS.OPENED:
        results = open_query(course_id, query)
    elif query.filter == PROBLEM_FILTERS.COMPLETED:
        results = completed_query(course_id, query)
    elif query.filter == PROBLEM_FILTERS.NOT_OPENED:
        results = not_open_query(course_id, query)
    elif query.filter == PROBLEM_FILTERS.NOT_COMPLETED:
        results = not_completed_query(course_id, query)
    return results


def get_section_users(course_id, query):
    """
    Gets Students filtered on specified section-specific query criteria
    """
    if query.filter == SECTION_FILTERS.OPENED:
        results = open_query(course_id, query)
    elif query.filter == SECTION_FILTERS.NOT_OPENED:
        results = not_open_query(course_id, query)
    return results


def make_existing_query(existing_queries):
    """
    Aggregates single queries in a group into one unified set of students
    """
    query = User.objects
    if existing_queries is None:
        return query

    query_dct = defaultdict(list)

    for existing_query in existing_queries:
        if existing_query == "" or existing_query == QUERYSTATUS.WORKING:
            continue
        inclusion_type = QueriesTemporary.objects.filter(id=existing_query)
        result = QueriesStudents.objects.filter(query_id=existing_query).values_list(DATABASE_FIELDS.STUDENT_ID, flat=True)
        if inclusion_type.exists():
            query_dct[inclusion_type[0].inclusion].append(result)

    for not_query in query_dct[INCLUSION_MAP.get(INCLUSION.NOT)]:
        query = query.exclude(id__in=not_query)

    for and_query in query_dct[INCLUSION_MAP.get(INCLUSION.AND)]:
        query = query.filter(id__in=and_query)

    or_query = User.objects
    qobjs = Q()
    for orq in query_dct[INCLUSION_MAP.get(INCLUSION.OR)]:
        qobjs = qobjs | (Q(id__in=orq))
    if len(query_dct[INCLUSION_MAP.get(INCLUSION.NOT)]) == 0 and len(query_dct[INCLUSION_MAP.get(INCLUSION.AND)]) == 0:
        return or_query.filter(qobjs)
    else:
        return query | or_query.filter(qobjs)


def not_open_query(course_id, query):
    """
    Specific db query for sections or problems that have not been opened
    """
    ids_in_course = CourseEnrollment.objects.filter(course_id=course_id, is_active=1).values_list(DATABASE_FIELDS.USER_ID)
    total_students = User.objects.filter(id__in=ids_in_course)
    without_open = total_students.exclude(id__in=
    StudentModule.objects.filter(
        module_state_key=query.entity_id,
        course_id=course_id).values_list(DATABASE_FIELDS.STUDENT_ID)
    )
    return process_results(course_id, without_open, DATABASE_FIELDS.ID, DATABASE_FIELDS.EMAIL)


def not_completed_query(course_id, query):
    """
    Specific db query for sections or problems that are not completed
    """
    ids_in_course = CourseEnrollment.objects.filter(course_id=course_id, is_active=1).values_list(DATABASE_FIELDS.USER_ID)
    total_students = User.objects.filter(id__in=ids_in_course)
    without_completed = total_students.exclude(id__in=
    StudentModule.objects.filter(
        module_state_key=query.entity_id,
        course_id=course_id).filter(~Q(grade=None)).values_list(DATABASE_FIELDS.STUDENT_ID)
    )
    return process_results(course_id, query, without_completed, DATABASE_FIELDS.ID, DATABASE_FIELDS.EMAIL)


def completed_query(course_id, query):
    """
    Specific db query for sections or problems that are completed
    """
    queryset = StudentModule.objects.filter(module_state_key=query.entity_id, course_id=course_id).filter(~Q(grade=None))
    return process_results(course_id, queryset, DATABASE_FIELDS.STUDENT_ID, DATABASE_FIELDS.STUDENT_EMAIL)


def open_query(course_id, query):
    """
    Specific db query for sections or problems that are opened
    """
    queryset = StudentModule.objects.filter(module_state_key=query.entity_id, course_id=course_id)
    return process_results(course_id, queryset, DATABASE_FIELDS.STUDENT_ID, DATABASE_FIELDS.STUDENT_EMAIL)


def process_results(course_id, queryset, id_field, email_field):
    """
    Handles any intermediate filtering between specific query criteria and returning to the user
    """
    filtered_query = filter_out_students_negative(course_id, queryset)
    values = filtered_query.values_list(id_field, email_field).distinct()
    return values


def filter_out_students_negative(course_id, queryset):
    """
    Exclude students who have opted out of emails and exclude students who are not active in the class
    Used specifically for positive queries i.e. have completed/opened because of query structure
    """
    without_opt_out = queryset.exclude(id__in=Optout.objects.all().values_list(DATABASE_FIELDS.USER_ID))
    without_not_enrolled = without_opt_out.exclude(id__in=
        CourseEnrollment.objects.filter(course_id=course_id, is_active=0).
        values_list(DATABASE_FIELDS.USER_ID))
    return without_not_enrolled


def filter_out_students_positive(course_id, queryset):
    """
    Exclude students who have opted out of emails and exclude students who are not active in the class
    Used specifically for negative queries i.e. not completed/not opened because of query structure
    """
    without_opt_out = queryset.exclude(student_id__in=Optout.objects.all().values_list(DATABASE_FIELDS.USER_ID))
    without_not_enrolled = without_opt_out.exclude(student_id__in=
        CourseEnrollment.objects.filter(course_id=course_id, is_active=0).
        values_list(DATABASE_FIELDS.USER_ID))
    return without_not_enrolled
