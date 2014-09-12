$(document).ready(function() {
    'use strict';

    // Variable for storing if a problem's analytics data has previously been retrieved.
    var elementsRetrieved = [];

    // We need to turn off, then on, all click handlers since the click handler gets attached each time the 
    // in-line analytics fragment is added; which is once per problem on the page.
    $('.instructor-analytics-action').off('click.inline-analytics').on('click.inline-analytics', function(event) {

        var elementId = this.id.substring(0, this.id.indexOf('_analytics_button'));
        var location = this.dataset.location;
        var answerDistUrl = this.dataset.answer_dist_url;

        // If data already retrieved for this problem, just show the div
        if (elementsRetrieved.indexOf(elementId) !== -1) {
            $('#' + elementId + '_analytics_close').show();
            return;
        }

        //Hide the error message div
        $('#' + elementId + '_analytics_error_message').hide();

        var partsToGet = [];
        var questionTypes = {}
        var correctResponses = {};
        var index;
        var id, partId;

        var divs = $('.' + elementId + '_analytics_div');

        // Construct array so we don't call the api for problems that have no questions supported by the api
        var arrayLength = divs.length;
        for (index = 0; index < arrayLength; index++) {
            id = divs[index].id;
            partId = id.substring(0, id.indexOf('_analytics'))
            if (divs[index].dataset.question_type !== 'None') {
                partsToGet.push(partId);
            }

            // Build dict of question types
            questionTypes[partId] = divs[index].dataset.question_type;

            // Build dict of correct responses
            correctResponses[partId] = divs[index].dataset.correct_response;
        }

        if (partsToGet.length > 0) {
            $.ajax({
                context: this,
                url: answerDistUrl,
                type: 'GET',
                data: {
                    module_id: location
                },
                dataType: 'json',

                success: function(response) {
                    if (response) {
                        process_response(response, partsToGet, questionTypes, correctResponses);
                        // Store that we retrieved data for this problem
                        elementsRetrieved.push(elementId);
                        // Show all the graphics
                        $('#' + elementId + '_analytics_close').show();
                    }
                },

                error: function(jqXHR, textStatus, errorThrown) {
                    $('#' + elementId + '_analytics_error_message').text(jqXHR.responseText).show();
                }
            });

        }
    });


    function process_response(response, partsToGet, questionTypes, correctResponses) {

        var dataByPart = response.data_by_part;
        var countByPart = response.count_by_part;
        var lastUpdateDate = response.last_update_date;
        var totalAttemptCount;
        var totalCorrectCount;
        var totalIncorrectCount;

        var partId;
        var index;

        // Render the appropriate analytics graphics for each part_id
        var arrayLength = partsToGet.length;
        for (index = 0; index < arrayLength; index++) {
            partId = partsToGet[index];

            if (countByPart[partId]) {
                totalAttemptCount = countByPart[partId][0];
                totalCorrectCount = countByPart[partId][1];
                totalIncorrectCount = countByPart[partId][2];
            } else {
                totalAttemptCount = 0;
                totalCorrectCount = 0;
                totalIncorrectCount = 0;
            }

            if (questionTypes[partId] === 'radio') {
                render_radio_analytics(dataByPart[partId], partId, totalAttemptCount, totalCorrectCount, totalIncorrectCount, correctResponses[partId], lastUpdateDate);
            } else if (questionTypes[partId] === 'checkbox') {
                render_checkbox_analytics(dataByPart[partId], partId, totalAttemptCount, totalCorrectCount, totalIncorrectCount, correctResponses[partId], lastUpdateDate);
            } else {
                // Just set the text on the div
                set_count_and_date(partId, totalAttemptCount, totalCorrectCount, totalIncorrectCount, lastUpdateDate, false)
            }
        }
    }


    function render_radio_analytics(result, partId, totalAttemptCount, totalCorrectCount, totalIncorrectCount, correctResponse, lastUpdateDate) {

        var valueId;
        var currentIndex;
        var valueIndex;
        var lastIndex;
        var correct;
        var count;
        var percent;
        var answerClass;
        var index;
        var tr;
        var trs = [];
        var lastRow = $('#' + partId + '_table tr:last');

        // Build the array of choice texts
        var choiceText = get_choice_texts(partId);

        if (result) {
            // Loop through results and construct row array
            var arrayLength = result.length;
            for (index = 0; index < arrayLength; index++) {

                valueId = result[index][0];
                currentIndex = index;
                valueIndex = valueId.replace('choice_', '');

                // Generate rows for gaps in answers in the results
                if (currentIndex < valueIndex) {
                    insert_missing_rows(partId, currentIndex, valueIndex, correctResponse, choiceText, trs);
                }

                correct = result[index][1];
                count = result[index][2];
                percent = Math.round(count * 1000 / (totalAttemptCount * 10));

                if (correct) {
                    answerClass = 'right';
                } else if (!correct) {
                    answerClass = 'wrong';
                }
                tr = $('<tr><td class="answer_box" title="' + choiceText[index] + '">' + (parseInt(index, 10) + 1) + '</td><td class="answer_box ' + answerClass + '"><span class="dot"></span></td><td class="answer_box">' + count + '</td><td class="answer_box">' + percent + '%</td></tr>');
                trs.push(tr[0]);
            }

            // Generate rows for missing answers at the end of results
            lastIndex = parseInt(result[result.length - 1][0].replace('choice_', ''), 10);
            if (lastIndex < choiceText.length - 1) {
                insert_missing_rows(partId, lastIndex + 1, choiceText.length, correctResponse, choiceText, trs);
            }

        } else {
            // There were no results
            trs = insert_missing_rows(partId, 0, choiceText.length, correctResponse, choiceText, trs);
        }

        // Append the row array to the table
        lastRow.after(trs);

        // Set student count and last_update_date
        set_count_and_date(partId, totalAttemptCount, totalCorrectCount, totalIncorrectCount, lastUpdateDate, true);

    }


    function insert_missing_rows(partId, currentIndex, finalIndex, correctResponse, choiceText, trs) {

        var answerClass;
        var tr;
        correctResponse = correctResponse.replace(/(^\[\')|(\'\]$)/g, '');

        while (currentIndex < finalIndex) {
            if ('choice_' + currentIndex == correctResponse) {
                answerClass = 'right';
            } else {
                answerClass = 'wrong';
            }
            tr = $('<tr><td class="answer_box" title="' + choiceText[currentIndex] + '">' + (currentIndex + 1) + '</td><td class="answer_box ' + answerClass + '"><span class="dot"></span></td><td class="answer_box">0</td><td class="answer_box">0%</td></tr>');
            trs.push(tr[0]);
            currentIndex += 1;
        }
        return trs;
    }


    function render_checkbox_analytics(result, partId, totalAttemptCount, totalCorrectCount, totalIncorrectCount, correctResponse, lastUpdateDate) {

        var count;
        var percent;
        var answerClass;
        var actualResponse;
        var imaginedResponse;
        var checkboxChecked;
        var countRow;
        var index;
        var maxColumns = 10;
        var choiceCounter = 1;
        var tr;
        var choiceTrs = [];
        var headerTrs = [];
        var dataTrs = [];

        // Construct the array of choice texts
        var choiceText = get_choice_texts(partId);

        // Add "Last Attempt" to the choice number column
        $('#' + partId + '_table .checkbox_header_row').after('<tr><td id="last_attempt" class="answer_box checkbox_last_attempt">Last Attempt</td></tr>');

        // Contruct the choice number column array
        while (choiceCounter <= choiceText.length) {
            tr = $('<tr><td id="column0:row' + choiceCounter + '" class="answer_box" title="' + choiceText[choiceCounter - 1] + '">' + choiceCounter + '</td></tr>');
            choiceTrs.push(tr[0]);
            choiceCounter += 1;
        }

        // Append the choice number column array to the header row
        var headerRow = $('#' + partId + '_table .checkbox_header_row');
        headerRow.after(choiceTrs);

        // Loop through results constructing header row and data row arrays
        if (result) {
            // Sort the results in decending response count order
            result.sort(order_by_count);

            var arrayLength = result.length;
            for (index = 0; index < arrayLength; index++) {
                // Append columns to the header row array
                tr = $('<th width="65px"></th>');
                headerTrs.push(tr[0]);

                // Append message and break if number of distinct choices >= max_columns
                if (index >= maxColumns) {
                    var notDisplayed = result.length - maxColumns;
                    tr = $('<th width="400px"> ' + notDisplayed + ' columns not displayed.</th>');
                    headerTrs.push(tr[0]);
                    break;
                }

                actualResponse = result[index][0];
                choiceCounter = 1;

                // Construct the data row array from student responses
                while (choiceCounter <= choiceText.length) {
                    imaginedResponse = 'choice_' + (choiceCounter - 1);

                    // Can't rely in contains method in all browsers so use indexOf
                    if ((correctResponse.indexOf(imaginedResponse) === -1) &&
                        (actualResponse.indexOf(imaginedResponse) === -1) ||
                        (correctResponse.indexOf(imaginedResponse) > -1 &&
                            actualResponse.indexOf(imaginedResponse) > -1)) {

                        answerClass = 'right';
                    } else {
                        answerClass = 'wrong';
                    }
                    if (actualResponse.indexOf(imaginedResponse) != -1) {
                        checkboxChecked = '<span class="dot"></span>';
                    } else {
                        checkboxChecked = '';
                    }
                    tr = $('<td id="column' + index + ':row' + choiceCounter + '" class="answer_box ' + answerClass + '">' + checkboxChecked + '</td>');
                    dataTrs.push([choiceCounter, tr[0]]);

                    choiceCounter += 1;
                }

                // Construct the Last Attempt row
                count = result[index][2];
                percent = Math.round(count * 1000 / (totalAttemptCount * 10));
                countRow += '<td class="answer_box">' + count + '<br/>' + percent + '%</td>'
            }

            // Append the header row array to the header row
            $('#' + partId + '_table tr:eq(0)').append(headerTrs);

            // Construct row array from the data array and append to the appropriate row in the table
            choiceCounter = 1;
            var rowArray = [];
            while (choiceCounter <= choiceText.length) {
                for (index = 0; index < dataTrs.length; index++) {
                    if (dataTrs[index][0] === choiceCounter) {
                        rowArray.push(dataTrs[index][1]);
                    }
                }
                $('#' + partId + '_table tr:eq(' + choiceCounter + ')').append(rowArray);
                rowArray = [];

                choiceCounter += 1;
            }

        }
        // Append count row to the last attempt row
        $('#' + partId + '_table #last_attempt').after(countRow);

        // Set student count and last_update_date
        set_count_and_date(partId, totalAttemptCount, totalCorrectCount, totalIncorrectCount, lastUpdateDate, true);

    }


    $('.analytics_close_button').off('click.inline-analytics').on('click.inline-analytics', function(event) {
        this.style.display = 'none';
    });


    function get_choice_texts(partId) {
        var choiceText = [];
        $('#inputtype_' + partId).find("fieldset label").each(function(index) {
            choiceText[index] = $(this).text();
        });
        return choiceText;
    }

    function set_count_and_date(partId, totalAttemptCount, totalCorrectCount, totalIncorrectCount, lastUpdateDate, graphicsFlag) {
        var part = document.getElementById(partId + '_analytics');
        part = $(part);
        part.find('.num-students').text(totalAttemptCount);
        part.find('.last-update').text(lastUpdateDate);

        if (graphicsFlag === false) {
            var correctPercent = Math.round(totalCorrectCount * 1000 / (totalAttemptCount * 10));
            var incorrectPercent = Math.round(totalIncorrectCount * 1000 / (totalAttemptCount * 10));
            part.find('.num-students-extra').text(totalCorrectCount + ' (' + correctPercent + '%) correct and ' + totalIncorrectCount + ' (' + incorrectPercent + '%) incorrect.')
        }
    }


    function order_by_count(a, b) {
        if (a[2] > b[2]) {
            return -1;
        }
        if (a[2] < b[2]) {
            return 1;
        }
        return 0;
    }

}());