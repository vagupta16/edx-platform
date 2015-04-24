window.InlineVideoAnalytics = (function() {


    'use strict';

    function processResponse(response) {
    	
    	console.log("In processResponse");
    	$('.inline-analytics-video_block').text('123213213');
    	
    	
    	var dataset = [ 5, 20, 35, 50, 65 ];
    //	d3.select('.inline-analytics-video_block').append("p").text("New paragraph!");
    	
   // 	d3.select('.inline-analytics-video_block').selectAll("p");
    	
//        .data(dataset)
//        .enter()
//        .append("p")
//        .text(function(d) { return d; })
//        .style("color", "red");
    	
    	
    	
//    	d3.select('.inline-analytics-video_block').selectAll("div")
//        .data(dataset)
//        .enter()
//        .append("div")
//        .attr("width", "20px")
//        .attr("background-color", "red")
//        .attr("height", "75px");
    	
    	var svg = d3.select(".inline-analytics-video_block").append("svg");
    	
//    	svg.selectAll("circle")
//        .data(dataset)
//        .enter()
//        .append("circle")
//        .attr("cx", function(d, i) {
//            return (i * 50) + 25;
//        });
    	
    	svg.selectAll(".bar")
        .data(dataset)
        .enter().append("rect")
        .attr("x", function(d, i) { return i * 20; })
        .attr("width", 5)
        .attr("height", function(d) { return d; })
        .style("fill", "red");
    	
//        svg.attr("width", 100)
//        .attr("height", 200)
//        .append("rect")
//        .attr("x", 100 )
//        .attr("width", 18)
//        .attr("height", 180)
//        .style("fill", "red");
    	
   //     .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    	
    	
    }
    		
    
    function processResponse2(response) {
    	
    	var data = d3.values(response.data);
    	console.log(data);
    	var videoSettings = d3.values(response.video_settings);
    	var seekInterval = 0;
    	
    	for (var index = 0; index < videoSettings.length; index++) {
    		if (videoSettings[index]['name'] === 'seek_interval') {
    			seekInterval = videoSettings[index]['value'];
    			break;
    		}
    	}
    	
        var youtubeId = Video.previousState.metadata[Object.keys(Video.previousState.metadata)[0]].id;
        console.log(youtubeId);
        
        var duration = Video.previousState.metadata[youtubeId].duration;
        console.log(duration);
    	
        var margin = {top: 20, right: 20, bottom: 30, left: 40};
        var width = $('.inline-analytics-video_block').parent().width() - margin.left - margin.right;
        var height = 250 - margin.top - margin.bottom;
        var parseDate = d3.time.format("%Y-%m-%d").parse;
        var color = d3.scale.category10();
        var barWidth = 10; //(width-300)/(duration/analytics_granularity);
        var barPadding = 1;
        
        var x = d3.scale.linear()
        .range([20, width - 40])
        .domain([0, duration]);


        var y = d3.scale.linear()
        .rangeRound([height, 0])
        .domain([0, d3.max(data, function(d) { return d.total_activity; })]);
    	

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");
        
        
        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left")
            .tickFormat(d3.format(",.0d"));
    	
        var svg = d3.select(".inline-analytics-video_block").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
        
    	
    	svg.selectAll(".bar")
        .data(data)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", function(d) { return x(d.seek_interval);}) // + barWidth/2);})
        .attr("width", barWidth - barPadding)              //  barWidth - barPadding) //     x(barWidth) + "px";)
        .attr("y", function(d) {return y(d.total_activity);})
        .attr("height", function(d) { return y(0) - y(d.total_activity);})
        .style("fill", "teal");
    	
   

    	
        svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate("+  barWidth/2 +"," +height + ")")
        .call(xAxis);
    
        svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Count");	
    

        
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
            
         //   console.log(location);
         //   console.log(answerDistUrl);
         //   console.log(courseId);
            
            location = Video.previousState.id;
            console.log(location);
            
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
                contentType: 'application/json',
                
                success: function(response) {
                    if (response) {
                    	window.InlineVideoAnalytics.processResponse2(response);
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
    	processResponse2: processResponse2,
        runDocReady: runDocReady,
        
        
    };

})();