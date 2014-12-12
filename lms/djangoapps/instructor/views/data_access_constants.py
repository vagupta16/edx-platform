"""
Constants and Query definition associated with data_access
"""
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


class INCLUSION:
    """
    Options for combining queries
    """
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    FILTER = "FILTER"


INCLUSION_MAP = {INCLUSION.AND: 'A',
                 INCLUSION.OR: 'O',
                 INCLUSION.NOT: 'N',
                 INCLUSION.FILTER: 'F'}


REVERSE_INCLUSION_MAP = {'A': INCLUSION.AND,
                         'O': INCLUSION.OR,
                         'N': INCLUSION.NOT,
                         'F': INCLUSION.FILTER}


class SECTION_FILTERS:
    """
    Possible filters we may have for sections
    """
    OPENED = "Opened"
    NOT_OPENED = "Not Opened"
    COMPLETED = "Completed"


class PROBLEM_FILTERS:
    """
    Possible filters we may have for problems
    """
    OPENED = SECTION_FILTERS.OPENED
    NOT_OPENED = SECTION_FILTERS.NOT_OPENED
    COMPLETED = "Completed"
    NOT_COMPLETED = "Not Completed"
    SCORE = "Score"
    NUMBER_PEER_GRADED = "Number peer graded"


class QUERY_TYPE:
    """
    Types for queries
    """
    SECTION = "Section"
    PROBLEM = "Problem"


class DATABASE_FIELDS:
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


class QUERYSTATUS:
    """
    Stores possible statuses for queries
    """
    WORKING = "working"
    COMPLETED = "completed"
