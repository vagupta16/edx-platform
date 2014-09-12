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
    valid_group_nodes = []
    if settings.ANALYTICS_ANSWER_DIST_URL and isinstance(block, CapaModule):
        responses = block.lcp.responders.values()
        valid_responses = {}
        rerandomize = False
        if block.rerandomize != 'never':
            rerandomize = True

        valid_types = settings.INLINE_ANALYTICS_SUPPORTED_TYPES
        
        # Categorize response type; 'other' if not supported by the analytics api
        for response in responses:
            response_type = 'other'
            
            # Build list of group nodes supported by the analytics api
            valid_group_nodes.extend(response.allowed_inputfields)
            
            for type, code in valid_types:
                if type == response.__class__.__name__:
                    response_type = code
                    break
   
            # Determine the part id and correct answer
            response_answers = response.get_answers().items()
            if len(response_answers):
                part_id, correct_response = response.get_answers().items()[0]
                valid_responses[part_id] = [correct_response, response_type]

        if valid_responses:

            # Loop through all the nodes finding the group elements for each response
            # We need to do this to get the responses in the same order as on the page
            for node in block.lcp.tree.iter(tag=etree.Element):
                part_id = node.attrib.get('id', None)
                if part_id and part_id in list(valid_responses) and node.tag in valid_group_nodes:
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
