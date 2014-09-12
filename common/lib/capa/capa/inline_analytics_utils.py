from lxml import etree

from django.conf import settings

from capa.responsetypes import ChoiceResponse, MultipleChoiceResponse, OptionResponse, NumericalResponse, StringResponse, FormulaResponse
from xmodule.capa_module import CapaModule

def get_responses_data(block):
    """
    Gets Capa data for questions; used by the in-line analytics display.
    
    Currently supported question types, for in-line analytics are:
       - checkboxgroup
       - choicegroup

    Problems with randomize are not currently supported for in-line analytics.
    If settings.ANALYTICS_ANSWER_DIST_URL is unset then returns None
    """
    responses_data = []
    if settings.ANALYTICS_ANSWER_DIST_URL and isinstance(block, CapaModule):
        responses = block.lcp.responders.values()
        valid_responses = {}
        rerandomize = False
        if block.rerandomize != 'never':
            rerandomize = True

        # Each response is an individual question
        for response in responses:
            question_type = None
            # Categorize response type if supported by the analytics api
            if isinstance(response, MultipleChoiceResponse):
                question_type = 'radio'
            elif isinstance(response, ChoiceResponse):
                question_type = 'checkbox'
            elif isinstance(response, OptionResponse):
                question_type = 'option'
            elif isinstance(response, NumericalResponse):
                question_type = 'numerical'
            elif isinstance(response, StringResponse):
                question_type = 'string'
            elif isinstance(response, FormulaResponse):
                question_type = 'formula'
            else:
                # Response types not supported by the analytics api categorized as "other"
                question_type == 'other'

            # Only radio and checkbox types are supported for in-line analytics graphics at this time
            # Option, numerical, string and formula are supported for number of students answered and date last updated
            if question_type:
                # There is only 1 part_id and correct response for each question
                part_id, correct_response = response.get_answers().items()[0]
                valid_responses[part_id] = [correct_response, question_type, ]

        if valid_responses:
            part_id = None
            
            # List of response types supported by the analytics api
            valid_types = ['checkboxgroup', 'choicegroup', 'optioninput', 'textline', 'formulaequationinput', 'textline']

            # Loop through all the nodes finding the group elements for each response
            # We need to do this to get the responses in the same order as on the page
            for node in block.lcp.tree.iter(tag=etree.Element):
                part_id = node.attrib.get('id', None)
                if part_id and part_id in list(valid_responses) and node.tag in valid_types:
                    # This is a valid question according to the list of valid responses and we have the group node
                    
                    if valid_responses[part_id][1] == 'other':
                        # Response type is not supported by the analytics api
                        responses_data.append([part_id, None, None, "The analytics cannot be displayed for this type of question."])
                    elif rerandomize:
                        # Response, actually the problem, has rerandomize != 'never'
                        responses_data.append([part_id, valid_responses[part_id][0], valid_responses[part_id][1], "The analytics cannot be displayed for this question as it uses randomize."])
                    else:
                        # Response is supported by the analytics api and rerandomize == 'never'
                        responses_data.append([part_id, valid_responses[part_id][0], valid_responses[part_id][1], None])

    return responses_data
