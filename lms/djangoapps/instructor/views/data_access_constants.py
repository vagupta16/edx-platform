"""
Constants and Query definition associated with data_access
"""
import re


class Query:
    """
    Encapsulates a query in the instructor dashboard email lists tool
    """
    def __init__(self, query_type, inclusion, entity_id, filtering, entity_name):
        self.type = query_type
        self.inclusion = inclusion
        self.entity_id = entity_id
        self.filter = filtering
        self.entity_name = entity_name


class Inclusion:
    """
    Options for combining queries
    """
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    FILTER = "FILTER"


INCLUSION_MAP = {Inclusion.AND: 'A',
                 Inclusion.OR: 'O',
                 Inclusion.NOT: 'N',
                 Inclusion.FILTER: 'F'}


REVERSE_INCLUSION_MAP = {'A': Inclusion.AND,
                         'O': Inclusion.OR,
                         'N': Inclusion.NOT,
                         'F': Inclusion.FILTER}

INCLUDE_SECTION_PATTERN = re.compile('chapter|sequential')
INCLUDE_PROBLEM_PATTERN = re.compile('problem')


class SectionFilters:  # pylint: disable=invalid-name
    """
    Possible filters we may have for sections
    """
    OPENED = "Opened"
    NOT_OPENED = "Not Opened"
    COMPLETED = "Completed"


class ProblemFilters:  # pylint: disable=invalid-name
    """
    Possible filters we may have for problems
    """
    OPENED = SectionFilters.OPENED
    NOT_OPENED = SectionFilters.NOT_OPENED
    COMPLETED = "Completed"
    NOT_COMPLETED = "Not Completed"
    SCORE = "Score"
    NUMBER_PEER_GRADED = "Number peer graded"


class QueryType:  # pylint: disable=invalid-name
    """
    Types for queries
    """
    SECTION = "Section"
    PROBLEM = "Problem"


class DatabaseFields:  # pylint: disable=invalid-name
    """
    Database columns
    """
    STUDENT_ID = "student_id"
    STUDENT_EMAIL = "student__email"
    ID = "id"
    EMAIL = "email"
    QUERY_ID = "query_id"
    QUERY = "query"
    USER_ID = "user_id"
    PROFILE_NAME = "profile__name"


class QueryStatus:  # pylint: disable=invalid-name
    """
    Stores possible statuses for queries
    """
    WORKING = "working"
    COMPLETED = "completed"
