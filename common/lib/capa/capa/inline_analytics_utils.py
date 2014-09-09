from lxml import etree

from django.conf import settings

from capa.responsetypes import ChoiceResponse, MultipleChoiceResponse
from xmodule.capa_module import CapaModule

def get_responses_data(block):
    """
    Gets Capa data for questions; used by the in-line analytics display.
    
    Currently supported question types, for in-line analytics are:
       - checkboxgroup
       - choicegroup

    Questions with shuffle are not currently supported for in-line analytics.
    If settings.ANALYTICS_ANSWER_DIST_URL is unset then returns None
    """
    responses_data = []
    if settings.ANALYTICS_ANSWER_DIST_URL and isinstance(block, CapaModule):
        responses = block.lcp.responders.values()
        valid_responses = {}

        # Each response is an individual question
        for response in responses:
            question_type = None
            has_shuffle = response.has_shuffle()
            if isinstance(response, MultipleChoiceResponse):
                question_type = 'radio'
            elif isinstance(response, ChoiceResponse):
                question_type = 'checkbox'

            # Only radio and checkbox types are support for in-line analytics at this time
            if question_type:
                # There is only 1 part_id and correct response for each question
                part_id, correct_response = response.get_answers().items()[0]
                valid_responses[part_id] = [correct_response, question_type, has_shuffle]

        if valid_responses:
            part_id = None

            # Loop through all the nodes finding the group elements for each question
            # We need to do this to get the questions in the same order as on the page
            for node in block.lcp.tree.iter(tag=etree.Element):
                part_id = node.attrib.get('id', None)
                if part_id and part_id in list(valid_responses) and node.tag in ['checkboxgroup', 'choicegroup']:
                    # This is a valid question according to the list of valid responses and we have the group node
                    # add part_id, correct_response, question_type, has_shufle
                    responses_data.append([part_id, valid_responses[part_id][0], valid_responses[part_id][1], valid_responses[part_id][2]])

    return responses_data