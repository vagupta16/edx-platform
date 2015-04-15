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
    	
    	var data = d3.values(response);
    	console.log(data);
    	var analytics_granularity = 10;
    	
    	
        var youtubeId = Video.previousState.metadata[Object.keys(Video.previousState.metadata)[0]].id;
        console.log(youtubeId);
        
        var duration = Video.previousState.metadata[youtubeId].duration;
        console.log(duration);
        duration = 450;
    	
    	
    //    var data = [ 5, 20, 35, 50, 65, 70, 65, 50, 90, 100, 70, 65, 50, 35, 20];
        var margin = {top: 20, right: 20, bottom: 30, left: 40};
        var width = $('.inline-analytics-video_block').parent().width() - margin.left - margin.right;
        var height = 500 - margin.top - margin.bottom;
        var parseDate = d3.time.format("%Y-%m-%d").parse;
        var color = d3.scale.category10();
        var barWidth = (width-300)/(duration/analytics_granularity);
        var barPadding = 1;
        
        
    	
        var x = d3.scale.linear()
        .range([20, width-70])
        .domain([0, duration]);

        var y = d3.scale.linear()
        .rangeRound([height, 0])
        .domain([0, d3.max(data, function(d) { return d.total_activity; })]);
    	
        //these colors don't exactly correspond to the exact elements in the graph but to generate them
        //we read the header to generate the colors
//        var header = d3.keys(data[0]);
//        var coloredHeader = header.map(color);
//
//        var color = d3.scale.ordinal()
//            .range(coloredHeader);

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
        
 //       color.domain(d3.keys(data[0]).filter(function(key) { return key !== "Date"; }));
        
        //x.domain(d3.extent(data, function(d) { return d.count(); }));
        //y.domain([0, d3.max(data, function(d) { return d; })]);
        
        
//        data.forEach(function(d) {
//            d.date = parseDate(d.Date);
//            var y0 = 0;
//            d.counts = color.domain().map(function(name) {
//                return {
//                    name: name, y0: y0, y1: y0 += +d[name]}; });
//            d.total = d.counts[d.counts.length - 1].y1;
//        });
        
        
//    	svg.selectAll(".bar")
//        .data(data)
//        .enter().append("rect")
//        .attr("x", function(d, i) { return i * 20; })
//        .attr("width", 15)
//        .attr("height", function(d) { return d; })
//        .style("fill", "red");
    	
    	svg.selectAll(".bar")
        .data(data)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", function(d) { return x(d.seek_interval - barWidth/2);})
        .attr("width", barWidth - barPadding) // function(d, i) { return analytics_granularity - barPadding;})
        .attr("y", function(d) {return y(d.total_activity);})
        .attr("height", function(d) { return y(0) - y(d.total_activity);})
        .style("fill", "teal");
    	
    	
        
   //     x.domain(d3.extent(data, function(d) { return d; }));
   //     y.domain([0, d3.max(data, function(d) { return d; })]); 	
   

    	
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