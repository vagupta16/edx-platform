# Common utilities for instructor dashboard components.

# reverse arguments on common functions to enable
# better coffeescript with callbacks at the end.
plantTimeout = (ms, cb) -> setTimeout cb, ms
plantInterval = (ms, cb) -> setInterval cb, ms


# get jquery element and assert its existance
find_and_assert = ($root, selector) ->
  item = $root.find selector
  if item.length != 1
    console.error "element selection failed for '#{selector}' resulted in length #{item.length}"
    throw "Failed Element Selection"
  else
    item

# standard ajax error wrapper
#
# wraps a `handler` function so that first
# it prints basic error information to the console.
std_ajax_err = (handler) -> (jqXHR, textStatus, errorThrown) ->
  console.warn """ajax error
                  textStatus: #{textStatus}
                  errorThrown: #{errorThrown}"""
  handler.apply this, arguments


# render a task list table to the DOM
# `$table_tasks` the $element in which to put the table
# `tasks_data`
create_task_list_table = ($table_tasks, tasks_data) ->
  $table_tasks.empty()

  options =
    enableCellNavigation: true
    enableColumnReorder: false
    autoHeight: true
    rowHeight: 100
    forceFitColumns: true

  columns = [
    id: 'task_type'
    field: 'task_type'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task Type')
    minWidth: 102
  ,
    id: 'task_input'
    field: 'task_input'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task inputs')
    minWidth: 150
  ,
    id: 'task_id'
    field: 'task_id'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task ID')
    minWidth: 150
  ,
    id: 'requester'
    field: 'requester'
    ###
    Translators: a "Requester" is a username that requested a task such as sending email
    ###
    name: gettext('Requester')
    minWidth: 80
  ,
    id: 'created'
    field: 'created'
    ###
    Translators: A timestamp of when a task (eg, sending email) was submitted appears after this
    ###
    name: gettext('Submitted')
    minWidth: 120
  ,
    id: 'duration_sec'
    field: 'duration_sec'
    ###
    Translators: The length of a task (eg, sending email) in seconds appears this
    ###
    name: gettext('Duration (sec)')
    minWidth: 80
  ,
    id: 'task_state'
    field: 'task_state'
    ###
    Translators: The state (eg, "In progress") of a task (eg, sending email) appears after this.
    ###
    name: gettext('State')
    minWidth: 80
  ,
    id: 'status'
    field: 'status'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task Status')
    minWidth: 80
  ,
    id: 'task_message'
    field: 'task_message'
    ###
    Translators: a "Task" is a background process such as grading students or sending email
    ###
    name: gettext('Task Progress')
    minWidth: 120
  ]

  table_data = tasks_data

  $table_placeholder = $ '<div/>', class: 'slickgrid'
  $table_tasks.append $table_placeholder
  grid = new Slick.Grid($table_placeholder, table_data, columns, options)

# Formats the subject field for email content history table
subject_formatter = (row, cell, value, columnDef, dataContext) ->
  if value is null then return gettext("An error occurred retrieving your email. Please try again later, and contact technical support if the problem persists.")
  subject_text = $('<span>').text(value['subject']).html()
  return '<p><a href="#email_message_' + value['id']+ '" id="email_message_' + value['id'] + '_trig">' + subject_text + '</a></p>'

# Formats the author field for the email content history table
sent_by_formatter = (row, cell, value, columnDef, dataContext) ->
  if value is null then return "<p>" + gettext("Unknown") + "</p>" else return '<p>' + value + '</p>'

# Formats the created field for the email content history table
created_formatter = (row, cell, value, columnDef, dataContext) ->
  if value is null then return "<p>" + gettext("Unknown") + "</p>" else return '<p>' + value + '</p>'

# Formats the number sent field for the email content history table
number_sent_formatter = (row, cell, value, columndDef, dataContext) ->
  if value is null then return "<p>" + gettext("Unknown") + "</p>" else return '<p>' + value + '</p>'

# Creates a table to display the content of bulk course emails
# sent in the past
create_email_content_table = ($table_emails, $table_emails_inner, email_data) ->
    $table_emails_inner.empty()
    $table_emails.show()

    options =
      enableCellNavigation: true
      enableColumnReorder: false
      autoHeight: true
      rowHeight: 50
      forceFitColumns: true

    columns = [
      id: 'email'
      field: 'email'
      name: gettext('Subject')
      minWidth: 80
      cssClass: "email-content-cell"
      formatter: subject_formatter
    ,
      id: 'requester'
      field: 'requester'
      name: gettext('Sent By')
      minWidth: 80
      maxWidth: 100
      cssClass: "email-content-cell"
      formatter: sent_by_formatter
    ,
      id: 'created'
      field: 'created'
      name: gettext('Time Sent')
      minWidth: 80
      cssClass: "email-content-cell"
      formatter: created_formatter
    ,
      id: 'number_sent'
      field: 'number_sent'
      name: gettext('Number Sent')
      minwidth: 100
      maxWidth: 150
      cssClass: "email-content-cell"
      formatter: number_sent_formatter
    ,
    ]

    table_data = email_data

    $table_placeholder = $ '<div/>', class: 'slickgrid'
    $table_emails_inner.append $table_placeholder
    grid = new Slick.Grid($table_placeholder, table_data, columns, options)
    $table_emails.append $ '<br/>'

# Creates the modal windows linked to each email in the email history
# Displayed when instructor clicks an email's subject in the content history table
create_email_message_views = ($messages_wrapper, emails) ->
  $messages_wrapper.empty()
  for email_info in emails

    # If some error occured, bail out
    if !email_info.email then return

    # Create hidden section for modal window
    email_id = email_info.email['id']
    $message_content = $('<section>', "aria-hidden": "true", class: "modal email-modal", id: "email_message_" + email_id)
    $email_wrapper = $ '<div>', class: 'inner-wrapper email-content-wrapper'
    $email_header = $ '<div>', class: 'email-content-header'

    # Add copy email body button
    $email_header.append $('<input>', type: "button", name: "copy-email-body-text", value: gettext("Copy Email To Editor"), id: "copy_email_" + email_id)

    $close_button = $ '<a>', href: '#', class: "close-modal"
    $close_button.append $ '<i>', class: 'icon-remove'
    $email_header.append $close_button

    # HTML escape the subject line
    subject_text = $('<span>').text(email_info.email['subject']).html()
    $email_header.append $('<h2>', class: "message-bold").html('<em>' + gettext('Subject:') + '</em> ' + subject_text)
    $email_header.append $('<h2>', class: "message-bold").html('<em>' + gettext('Sent By:') + '</em> ' + email_info.requester)
    $email_header.append $('<h2>', class: "message-bold").html('<em>' + gettext('Time Sent:') + '</em> ' + email_info.created)
    $email_header.append $('<h2>', class: "message-bold").html('<em>' + gettext('Sent To:') + '</em> ' + email_info.sent_to)
    $email_wrapper.append $email_header

    $email_wrapper.append $ '<hr>'

    # Last, add email content section
    $email_content = $ '<div>', class: 'email-content-message'
    $email_content.append $('<h2>', class: "message-bold").html("<em>" + gettext("Message:") + "</em>")
    $message = $('<div>').html(email_info.email['html_message'])
    $email_content.append $message
    $email_wrapper.append $email_content

    $message_content.append $email_wrapper
    $messages_wrapper.append $message_content

    # Setup buttons to open modal window and copy an email message
    $('#email_message_' + email_info.email['id'] + '_trig').leanModal({closeButton: ".close-modal", copyEmailButton: "#copy_email_" + email_id})
    setup_copy_email_button(email_id, email_info.email['html_message'], email_info.email['subject'])

# Helper method to set click handler for modal copy email button
setup_copy_email_button = (email_id, html_message, subject) ->
    $("#copy_email_" + email_id).click =>
        editor = tinyMCE.get("mce_0")
        editor.setContent(html_message)
        $('#id_subject').val(subject)


# Helper class for managing the execution of interval tasks.
# Handles pausing and restarting.
class IntervalManager
  # Create a manager which will call `fn`
  # after a call to .start every `ms` milliseconds.
  constructor: (@ms, @fn) ->
    @intervalID = null

  # Start or restart firing every `ms` milliseconds.
  start: ->
    @fn()
    if @intervalID is null
      @intervalID = setInterval @fn, @ms

  # Pause firing.
  stop: ->
    clearInterval @intervalID
    @intervalID = null


class PendingInstructorTasks
  ### Pending Instructor Tasks Section ####
  constructor: (@$section) ->
    # Currently running tasks
    @$running_tasks_section = find_and_assert @$section, ".running-tasks-section"
    @$table_running_tasks = find_and_assert @$section, ".running-tasks-table"
    @$no_tasks_message = find_and_assert @$section, ".no-pending-tasks-message"

    # start polling for task list
    # if the list is in the DOM
    if @$table_running_tasks.length
      # reload every 20 seconds.
      TASK_LIST_POLL_INTERVAL = 20000
      @reload_running_tasks_list()
      @task_poller = new IntervalManager(TASK_LIST_POLL_INTERVAL, => @reload_running_tasks_list())

  # Populate the running tasks list
  reload_running_tasks_list: =>
    list_endpoint = @$table_running_tasks.data 'endpoint'
    $.ajax
      dataType: 'json'
      url: list_endpoint
      success: (data) =>
        if data.tasks.length
          create_task_list_table @$table_running_tasks, data.tasks
          @$no_tasks_message.hide()
          @$running_tasks_section.show()
        else
          console.log "No pending instructor tasks to display"
          @$running_tasks_section.hide()
          @$no_tasks_message.empty()
          @$no_tasks_message.append $('<p>').text gettext("No tasks currently running.")
          @$no_tasks_message.show()
      error: std_ajax_err => console.error "Error finding pending instructor tasks to display"
    ### /Pending Instructor Tasks Section ####

class KeywordValidator

    @keyword_regex = /%%+[^%]+%%/g
    @keywords = [
      '%%USER_ID%%',
      '%%USER_FULLNAME%%',
      '%%COURSE_DISPLAY_NAME%%',
      '%%COURSE_ID%%',
      '%%COURSE_START_DATE%%',
      '%%COURSE_END_DATE%%'
    ]

    @validate_string: (string) =>
      regex_match = string.match(@keyword_regex)
      found_keywords = if regex_match == null then [] else regex_match
      invalid_keywords = []
      is_valid = true
      keywords = @keywords

      for found_keyword in found_keywords
        do (found_keyword) ->
          if found_keyword not in keywords
            invalid_keywords.push found_keyword
      
      if invalid_keywords.length != 0
        is_valid = false
      
      return {
        is_valid: is_valid,
        invalid_keywords: invalid_keywords
      }

# Helper class that encompasses static functions 
# for doing some math on reasonably small arrays
class Statistics
  @square: (x) -> x * x

  @sum_reducer: (accum, n) -> accum + n

  @get_zscore: (x, avg, stddev) -> (x - avg) / stddev

  @get_avg: (nums) ->
    if nums? and nums.length > 0
      return _.reduce(nums, Statistics.sum_reducer, 0) / nums.length
    else
      return 0

  @get_stddev: (nums) ->
    avg = Statistics.get_avg(nums)
    mean_differences = _.map(nums, (n) -> Statistics.square(n - avg))
    return Math.sqrt Statistics.get_avg mean_differences

# Base class for a Slickgrid Column Sorter
class DefaultNumericSorter
  constructor: (dataview) ->
    @dataview = dataview
    # constructor returns a callback fn that
    # can be passed into Slickgrid's onSort.subscribe
    return @callback

  callback: (e, args) =>
    @sortcol = args.sortCol.field
    console.log 'in callback', args
    @dataview.sort(@comparer, args.sortAsc)

  comparer: (a, b) =>
    x = a[@sortcol]
    y = b[@sortcol]
    return (x == y ? 0 : (x > y ? 1 : -1))

# Helper class that provides additional functions
# around data for SlickGrid
class SlickGridHelpers
  @capitalize: (str) -> str.charAt(0).toUpperCase() + str.slice(1)

  @update_rows_with_unique_ids: (data, id_getter_fn) ->
    for row in data
      row['id'] = id_getter_fn(row)

  @autogenerate_slickgrid_cols: (row, names={}, formatters={}, options={}) ->
    # Given an object representing a json row of data,
    # infers columns as keys. 
    #
    # Arguments:
    #
    #   row (dict): a representative sample row of the dataset
    #
    #   names (dict): (optional) a dict of key / values 
    #     representing attributes to their displayed col names
    #
    #   formatters (dict): (optional) a dict of key / values
    #     representing fields and their formatter constructors
    #
    # Returns:
    #     
    #   An array of objects that represent Slickgrid columns,
    #   suitable for passing to a Slickgrid constructor
    return _(row).chain()
        .keys()
        .map((attr) ->
            column_definition = {
              id: attr,
              name: if attr of names then names[attr] else SlickGridHelpers.capitalize(attr),
              field: attr,
              formatter: if attr of formatters then formatters[attr] else undefined,
              sortable: if _.isNaN(parseFloat(row[attr])) then false else true,
            }
            if attr in options
              _.extend(column_definition, options)
            return column_definition
        )
        .value()


# export for use
# create parent namespaces if they do not already exist.
# abort if underscore can not be found.
if _?
  _.defaults window, InstructorDashboard: {}
  window.InstructorDashboard.util =
    plantTimeout: plantTimeout
    plantInterval: plantInterval
    std_ajax_err: std_ajax_err
    IntervalManager: IntervalManager
    create_task_list_table: create_task_list_table
    create_email_content_table: create_email_content_table
    create_email_message_views: create_email_message_views
    PendingInstructorTasks: PendingInstructorTasks
    KeywordValidator: KeywordValidator
    SlickGridHelpers: SlickGridHelpers
    Statistics: Statistics
    DefaultNumericSorter: DefaultNumericSorter
