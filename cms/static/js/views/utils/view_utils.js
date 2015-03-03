/**
 * Provides useful utilities for views.
 */
define(["jquery", "underscore", "gettext", "js/views/feedback_notification", "js/views/feedback_prompt"],
    function ($, _, gettext, NotificationView, PromptView) {
        var toggleExpandCollapse, showLoadingIndicator, hideLoadingIndicator, confirmThenRunOperation,
            runOperationShowingMessage, disableElementWhileRunning, getScrollOffset, setScrollOffset,
            setScrollTop, redirect, reload, hasChangedAttributes, deleteNotificationHandler,
            validateRequiredField, validateURLItemEncoding, validateTotalKeyLength, checkTotalKeyLengthViolations;

        // see https://openedx.atlassian.net/browse/TNL-889 for what is it and why it's 65
        var MAX_SUM_KEY_LENGTH = 65;

        /**
         * Toggles the expanded state of the current element.
         */
        toggleExpandCollapse = function(target, collapsedClass) {
            // Support the old 'collapsed' option until fully switched over to is-collapsed
            if (!collapsedClass) {
                collapsedClass = 'collapsed';
            }
            target.closest('.expand-collapse').toggleClass('expand collapse');
            target.closest('.is-collapsible, .window').toggleClass(collapsedClass);
            target.closest('.is-collapsible').children('article').slideToggle();
        };

        /**
         * Show the page's loading indicator.
         */
        showLoadingIndicator = function() {
            $('.ui-loading').show();
        };

        /**
         * Hide the page's loading indicator.
         */
        hideLoadingIndicator = function() {
            $('.ui-loading').hide();
        };

        /**
         * Confirms with the user whether to run an operation or not, and then runs it if desired.
         */
        confirmThenRunOperation = function(title, message, actionLabel, operation, onCancelCallback) {
            return new PromptView.Warning({
                title: title,
                message: message,
                actions: {
                    primary: {
                        text: actionLabel,
                        click: function(prompt) {
                            prompt.hide();
                            operation();
                        }
                    },
                    secondary: {
                        text: gettext('Cancel'),
                        click: function(prompt) {
                            if (onCancelCallback) {
                                onCancelCallback();
                            }
                            return prompt.hide();
                        }
                    }
                }
            }).show();
        };

        /**
         * Shows a progress message for the duration of an asynchronous operation.
         * Note: this does not remove the notification upon failure because an error
         * will be shown that shouldn't be removed.
         * @param message The message to show.
         * @param operation A function that returns a promise representing the operation.
         */
        runOperationShowingMessage = function(message, operation) {
            var notificationView;
            notificationView = new NotificationView.Mini({
                title: gettext(message)
            });
            notificationView.show();
            return operation().done(function() {
                notificationView.hide();
            });
        };

        /**
         * Disables a given element when a given operation is running.
         * @param {jQuery} element the element to be disabled.
         * @param operation the operation during whose duration the
         * element should be disabled. The operation should return
         * a JQuery promise.
         */
        disableElementWhileRunning = function(element, operation) {
            element.addClass("is-disabled").attr('aria-disabled', true);
            return operation().always(function() {
                element.removeClass("is-disabled").attr('aria-disabled', false);
            });
        };

        /**
         * Returns a handler that removes a notification, both dismissing it and deleting it from the database.
         * @param callback function to call when deletion succeeds
         */
        deleteNotificationHandler = function(callback) {
            return function (event) {
                event.preventDefault();
                $.ajax({
                    url: $(this).data('dismiss-link'),
                    type: 'DELETE',
                    success: callback
                });
            };
        };

        /**
         * Performs an animated scroll so that the window has the specified scroll top.
         * @param scrollTop The desired scroll top for the window.
         */
        setScrollTop = function(scrollTop) {
            $('html, body').animate({
                scrollTop: scrollTop
            }, 500);
        };

        /**
         * Returns the relative position that the element is scrolled from the top of the view port.
         * @param element The element in question.
         */
        getScrollOffset = function(element) {
            var elementTop = element.offset().top;
            return elementTop - $(window).scrollTop();
        };

        /**
         * Scrolls the window so that the element is scrolled down to the specified relative position
         * from the top of the view port.
         * @param element The element in question.
         * @param offset The amount by which the element should be scrolled from the top of the view port.
         */
        setScrollOffset = function(element, offset) {
            var elementTop = element.offset().top,
                newScrollTop = elementTop - offset;
            setScrollTop(newScrollTop);
        };

        /**
         * Redirects to the specified URL. This is broken out as its own function for unit testing.
         */
        redirect = function(url) {
            window.location = url;
        };

        /**
         * Reloads the page. This is broken out as its own function for unit testing.
         */
        reload = function() {
            window.location.reload();
        };

        /**
         * Returns true if a model has changes to at least one of the specified attributes.
         * @param model The model in question.
         * @param attributes The list of attributes to be compared.
         * @returns {boolean} Returns true if attribute changes are found.
         */
        hasChangedAttributes = function(model, attributes) {
            var i, changedAttributes = model.changedAttributes();
            if (!changedAttributes) {
                return false;
            }
            for (i=0; i < attributes.length; i++) {
                if (_.has(changedAttributes, attributes[i])) {
                    return true;
                }
            }
            return false;
        };

        var keywordValidator = (function () {
            var regexp = /%%[^%\s]+%%/g;
            var keywordsSupported = [
                '%%USER_ID%%',
                '%%USER_FULLNAME%%',
                '%%COURSE_DISPLAY_NAME%%',
                '%%COURSE_ID%%',
                '%%COURSE_START_DATE%%',
                '%%COURSE_END_DATE%%'
            ];
            function validate(string) {
                var keywordsFound = string.match(regexp) || [];
                var keywordsInvalid = $.map(keywordsFound, function (keyword) {
                    if ($.inArray(keyword, keywordsSupported) === -1) {
                        return keyword;
                    } else {
                        // return `null` or `undefined` to remove an element
                        return undefined;
                    }
                });

                return {
                    'isValid': keywordsInvalid.length === 0,
                    'keywordsInvalid': keywordsInvalid
                }

            }
            return {
                'validateString': validate
            };
        }());

        /**
         * Helper method for course/library creation - verifies a required field is not blank.
         */
        validateRequiredField = function (msg) {
            return msg.length === 0 ? gettext('Required field.') : '';
        };

        /**
         * Helper method for course/library creation.
         * Check that a course (org, number, run) doesn't use any special characters
         */
        validateURLItemEncoding = function (item, allowUnicode) {
            var required = validateRequiredField(item);
            if (required) {
                return required;
            }
            if (allowUnicode) {
                if (/\s/g.test(item)) {
                    return gettext('Please do not use any spaces in this field.');
                }
            }
            else {
                if (item !== encodeURIComponent(item) || item.match(/[!'()*]/)) {
                    return gettext('Please do not use any spaces or special characters in this field.');
                }
            }
            return '';
        };

        // Ensure that sum length of key field values <= ${MAX_SUM_KEY_LENGTH} chars.
        validateTotalKeyLength = function (key_field_selectors) {
            var totalLength = _.reduce(
                key_field_selectors,
                function (sum, ele) { return sum + $(ele).val().length;},
                0
            );
            return totalLength <= MAX_SUM_KEY_LENGTH;
        };

        checkTotalKeyLengthViolations = function(selectors, classes, key_field_selectors, message_tpl) {
            if (!validateTotalKeyLength(key_field_selectors)) {
                $(selectors.errorWrapper).addClass(classes.shown).removeClass(classes.hiding);
                $(selectors.errorMessage).html('<p>' + _.template(message_tpl, {limit: MAX_SUM_KEY_LENGTH}) + '</p>');
                $(selectors.save).addClass(classes.disabled);
            } else {
                $(selectors.errorWrapper).removeClass(classes.shown).addClass(classes.hiding);
            }
        };

        return {
            'toggleExpandCollapse': toggleExpandCollapse,
            'showLoadingIndicator': showLoadingIndicator,
            'hideLoadingIndicator': hideLoadingIndicator,
            'confirmThenRunOperation': confirmThenRunOperation,
            'runOperationShowingMessage': runOperationShowingMessage,
            'disableElementWhileRunning': disableElementWhileRunning,
            'deleteNotificationHandler': deleteNotificationHandler,
            'setScrollTop': setScrollTop,
            'getScrollOffset': getScrollOffset,
            'setScrollOffset': setScrollOffset,
            'redirect': redirect,
            'reload': reload,
            'keywordValidator': keywordValidator,
            'hasChangedAttributes': hasChangedAttributes,
            'hasChangedAttributes': hasChangedAttributes,
            'validateRequiredField': validateRequiredField,
            'validateURLItemEncoding': validateURLItemEncoding,
            'validateTotalKeyLength': validateTotalKeyLength,
            'checkTotalKeyLengthViolations': checkTotalKeyLengthViolations
        };
    });
