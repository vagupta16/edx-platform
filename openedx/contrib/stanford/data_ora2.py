"""
Helpers for instructor dashboard, data download, ora2 report
"""


from django import db

from util.query import get_read_replica_cursor_if_available


def collect_anonymous_ora2_data(course_id):
    """
    Call collect_ora2_data for anonymized, aggregated ORA2 response data.
    """
    return collect_ora2_data(course_id, False)


def collect_email_ora2_data(course_id):
    """
    Call collect_ora2_data for aggregated ORA2 response data including users' email addresses
    """
    return collect_ora2_data(course_id, True)


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


def collect_ora2_data(course_id, include_email=False):
    """
    Query MySQL database for aggregated ora2 response data. include_email = False by default
    """
    cursor = get_read_replica_cursor_if_available(db)
    #Syntax unsupported by other vendors such as SQLite test db
    if db.connection.vendor != 'mysql':
        return '', ['']
    raw_queries = ora2_data_queries(include_email).split(';')
    cursor.execute(raw_queries[0])
    cursor.execute(raw_queries[1], [course_id])
    header = [item[0] for item in cursor.description]
    return header, cursor.fetchall()


# pylint: disable=invalid-name
def ora2_data_queries(include_email):
    """
    Wraps a raw SQL query which retrieves all ORA2 responses for a course.
    """

    RAW_QUERY = """
SET SESSION group_concat_max_len = 1000000;
SELECT `sub`.`uuid` AS `submission_uuid`,
`student`.`item_id` AS `item_id`,
{id_column},
`sub`.`submitted_at` AS `submitted_at`,
`sub`.`raw_answer` AS `raw_answer`,
(
    SELECT GROUP_CONCAT(
        CONCAT(
            "Assessment #", `assessment`.`id`,
            " -- scored_at: ", `assessment`.`scored_at`,
            " -- type: ", `assessment`.`score_type`,
            " -- scorer_id: ", `assessment`.`scorer_id`,
            IF(
                `assessment`.`feedback` != "",
                CONCAT(" -- overall_feedback: ", `assessment`.`feedback`),
                ""
            )
        )
        SEPARATOR '\n'
    )
    FROM `assessment_assessment` AS `assessment`
    WHERE `assessment`.`submission_uuid`=`sub`.`uuid`
    ORDER BY `assessment`.`scored_at` ASC
) AS `assessments`,
(
    SELECT GROUP_CONCAT(
        CONCAT(
            "Assessment #", `assessment`.`id`,
            " -- ", `criterion`.`label`,
            IFNULL(CONCAT(": ", `option`.`label`, " (", `option`.`points`, ")"), ""),
            IF(
                `assessment_part`.`feedback` != "",
                CONCAT(" -- feedback: ", `assessment_part`.`feedback`),
                ""
            )
        )
        SEPARATOR '\n'
    )
    FROM `assessment_assessment` AS `assessment`
    JOIN `assessment_assessmentpart` AS `assessment_part`
    ON `assessment_part`.`assessment_id`=`assessment`.`id`
    JOIN `assessment_criterion` AS `criterion`
    ON `criterion`.`id`=`assessment_part`.`criterion_id`
    LEFT JOIN `assessment_criterionoption` AS `option`
    ON `option`.`id`=`assessment_part`.`option_id`
    WHERE `assessment`.`submission_uuid`=`sub`.`uuid`
    ORDER BY `assessment`.`scored_at` ASC, `criterion`.`order_num` DESC
) AS `assessments_parts`,
(
    SELECT `created_at`
    FROM `submissions_score` AS `score`
    WHERE `score`.`submission_id`=`sub`.`id`
    ORDER BY `score`.`created_at` DESC LIMIT 1
) AS `final_score_given_at`,
(
    SELECT `points_earned`
    FROM `submissions_score` AS `score`
    WHERE `score`.`submission_id`=`sub`.`id`
    ORDER BY `score`.`created_at` DESC LIMIT 1
) AS `final_score_points_earned`,
(
    SELECT `points_possible`
    FROM `submissions_score` AS `score`
    WHERE `score`.`submission_id`=`sub`.`id`
    ORDER BY `score`.`created_at` DESC LIMIT 1
) AS `final_score_points_possible`,
(
    SELECT GROUP_CONCAT(`feedbackoption`.`text` SEPARATOR '\n')
    FROM `assessment_assessmentfeedbackoption` AS `feedbackoption`
    JOIN `assessment_assessmentfeedback_options` AS `feedback_join`
    ON `feedback_join`.`assessmentfeedbackoption_id`=`feedbackoption`.`id`
    JOIN `assessment_assessmentfeedback` AS `feedback`
    ON `feedback`.`id`=`feedback_join`.`assessmentfeedback_id`
    WHERE `feedback`.`submission_uuid`=`sub`.`uuid`
) AS `feedback_options`,
(
    SELECT `feedback_text`
    FROM `assessment_assessmentfeedback` as `feedback`
    WHERE `feedback`.`submission_uuid`=`sub`.`uuid`
    LIMIT 1
) AS `feedback`
FROM `submissions_submission` AS `sub`
JOIN `submissions_studentitem` AS `student` ON `sub`.`student_item_id`=`student`.`id`
WHERE `student`.`item_type`="openassessment" AND `student`.`course_id`=%s
    """
    if include_email:
        id_column = """
        (
            SELECT `auth_user`.`email`
            FROM `auth_user`
            JOIN `student_anonymoususerid` AS `anonymous`
            ON `auth_user`.`id` = `anonymous`.`user_id`
            WHERE `student`.`student_id` = `anonymous`.`anonymous_user_id`
        ) AS `email`
        """
    else:
        id_column = "`student`.`student_id` AS `anonymized_student_id`"

    return RAW_QUERY.format(id_column=id_column)
