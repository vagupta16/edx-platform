from courseware.models import StudentModule

class Query:
    def __init__(self, type, inclusion, id, filter):
        self.type= type
        self.inclusion= inclusion
        self.id = id
        self.filter = filter

class INCLUSION:
    AND="AND"
    OR="OR"
    NOT="NOT"

class SECTION_FILTERS:
    OPENED="OPENED"
    COMPLETED="COMPLETED"

class PROBLEM_FILTERS:
    OPENED="OPENED"
    COMPLETED="COMPLETED"
    SCORE="SCORE"
    NUMBER_PEER_GRADED="NUMBER_PEER_GRADED"

class QUERY_TYPE:
    SECTION="SECTION"
    PROBLEM="PROBLEM"
