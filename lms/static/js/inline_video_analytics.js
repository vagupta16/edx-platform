window.InlineVideoAnalytics = (function() {


    'use strict';

    function processResponse(response) {
    	
    	console.log("In processResponse");
    	$('.inline-analytics-video_block').text('123213213');
    }
    		
    		
    		
    function runDocReady(elementId) {
    	
        // Variable for storing if a problem's analytics data has previously been retrieved.
        var elementsRetrieved = [];
    	
        // Use elementId to attach handlers to the correct button since there
        // may be many problems on the page.
        $('#' + elementId + '_analytics_button').click(function(event) {

            var location = this.dataset.location;
            var answerDistUrl = this.dataset.answerDistUrl;
            var courseId = this.dataset.courseId;
            
            console.log(location);
            console.log(answerDistUrl);
            console.log(courseId);
            
            
            var data = {
            		module_id: location,
            		course_id: courseId,
            };
            
            $.ajax({
                context: this,
                url: answerDistUrl,
                type: 'POST',
                data: {data: JSON.stringify(data)},
                dataType: 'json',
                contentType: "application/json",
                
                success: function(response) {
                    if (response) {
                    	window.InlineVideoAnalytics.processResponse(response);
                   //     window.InlineAnalytics.processResponse(response, partsToGet, questionTypesByPart, correctResponses, choiceNameListByPart);
                        // Store that we retrieved data for this problem
                   //     elementsRetrieved.push(elementId);
                        // Show all the graphics
                   //     $('#' + elementId + '_analytics_close').show();
                    	console.log('success');
                    }
                },
                
                error: function(jqXHR) {
                  //  $('#' + elementId + '_analytics_error_message').html(jqXHR.responseText).show();
                	console.log('error');
                }
                
            });
           
           
    		
        });
    	
    }
    
    return {
    	processResponse: processResponse,
        runDocReady: runDocReady,
        
        
    };

})();