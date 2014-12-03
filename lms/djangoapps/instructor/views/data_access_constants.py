class Query:
    def __init__(self, type, inclusion, id, filter, entityName):
        self.type= type
        self.inclusion= inclusion
        self.id = id
        self.filter = filter
        self.entityName = entityName

class INCLUSION:
    AND="AND"
    OR="OR"
    NOT="NOT"
    FILTER="FILTER"

INCLUSION_MAP = {INCLUSION.AND : 'A',
                 INCLUSION.OR : 'O',
                 INCLUSION.NOT : 'N',
                 INCLUSION.FILTER:'F'}

REVERSE_INCLUSION_MAP = {'A' : INCLUSION.AND,
                         'O' : INCLUSION.OR,
                         'N' : INCLUSION.NOT,
                         'F' : INCLUSION.FILTER}

class SECTION_FILTERS:
    OPENED="Opened"
    NOT_OPENED = "Not Opened"
    COMPLETED="Completed"


class PROBLEM_FILTERS:
    OPENED= SECTION_FILTERS.OPENED
    NOT_OPENED = SECTION_FILTERS.NOT_OPENED
    COMPLETED="Completed"
    NOT_COMPLETED = "Not Completed"
    SCORE="Score"
    NUMBER_PEER_GRADED="Number peer graded"

class QUERY_TYPE:
    SECTION="Section"
    PROBLEM="Problem"

class DATABASE_FIELDS:
    STUDENT_ID = "student_id"
    STUDENT_EMAIL = "student__email"
    ID = "id"
    EMAIL = "email"
    QUERY_ID = "query_id"
    QUERY = "query"
    USER_ID = "user_id"
    PROFILE_NAME = "profile__name"

class QUERYSTATUS:
    WORKING ="working"
    COMPLETED = "completed"