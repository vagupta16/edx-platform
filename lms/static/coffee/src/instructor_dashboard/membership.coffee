###
Membership Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments
emailStudents = false


class MemberListWidget
  # create a MemberListWidget `$container` is a jquery object to embody.
  # `params` holds template parameters. `params` should look like the defaults below.
  constructor: (@$container, params={}) ->
    params = _.defaults params,
      title: "Member List"
      info: """
        Use this list to manage members.
      """
      labels: ["field1", "field2", "field3"]
      add_placeholder: "Enter name"
      add_btn_label: "Add Member"
      add_handler: (input) ->

    template_html = $("#member-list-widget-template").html()
    @$container.html Mustache.render template_html, params

    # bind add button
    @$('input[type="button"].add').click =>
      params.add_handler? @$('.add-field').val()

  # clear the input text field
  clear_input: -> @$('.add-field').val ''

  # clear all table rows
  clear_rows: -> @$('table tbody').empty()

  # takes a table row as an array items are inserted as text, unless detected
  # as a jquery objects in which case they are inserted directly. if an
  # element is a jquery object
  add_row: (row_array) ->
    $tbody = @$('table tbody')
    $tr = $ '<tr>'
    for item in row_array
      $td = $ '<td>'
      if item instanceof jQuery
        $td.append item
      else
        $td.text item
      $tr.append $td
    $tbody.append $tr

  # local selector
  $: (selector) ->
    if @debug?
      s = @$container.find selector
      if s?.length != 1
        console.warn "local selector '#{selector}' found (#{s.length}) results"
      s
    else
      @$container.find selector


class AuthListWidget extends MemberListWidget
  constructor: ($container, @rolename, @$error_section) ->
    super $container,
      title: $container.data 'display-name'
      info: $container.data 'info-text'
      labels: [gettext("Username"), gettext("Email"), gettext("Revoke access")]
      add_placeholder: gettext("Enter username or email")
      add_btn_label: $container.data 'add-button-label'
      add_handler: (input) => @add_handler input

    @debug = true
    @list_endpoint = $container.data 'list-endpoint'
    @modify_endpoint = $container.data 'modify-endpoint'
    unless @rolename?
      throw "AuthListWidget missing @rolename"

    @reload_list()

  # action to do when is reintroduced into user's view
  re_view: ->
    @clear_errors()
    @clear_input()
    @reload_list()

  # handle clicks on the add button
  add_handler: (input) ->
    if input? and input isnt ''
      @modify_member_access input, 'allow', (error) =>
        # abort on error
        return @show_errors error unless error is null
        @clear_errors()
        @clear_input()
        @reload_list()
    else
      @show_errors gettext "Please enter a username or email."

  # reload the list of members
  reload_list: ->
    # @clear_rows()
    @get_member_list (error, member_list) =>
      # abort on error
      return @show_errors error unless error is null

      # only show the list of there are members
      @clear_rows()

      # use _.each instead of 'for' so that member
      # is bound in the button callback.
      _.each member_list, (member) =>
        # if there are members, show the list

        # create revoke button and insert it into the row
        label_trans = gettext("Revoke access")
        $revoke_btn = $ _.template('<div class="revoke"><i class="icon-remove-sign"></i> <%= label %></div>', {label: label_trans}),
          class: 'revoke'
        $revoke_btn.click =>
            @modify_member_access member.email, 'revoke', (error) =>
              # abort on error
              return @show_errors error unless error is null
              @clear_errors()
              @reload_list()
        @add_row [member.username, member.email, $revoke_btn]

  # clear error display
  clear_errors: -> @$error_section?.text ''

  # set error display
  show_errors: (msg) -> @$error_section?.text msg

  # send ajax request to list members
  # `cb` is called with cb(error, member_list)
  get_member_list: (cb) ->
    $.ajax
      dataType: 'json'
      url: @list_endpoint
      data: rolename: @rolename
      success: (data) => cb? null, data[@rolename]
      error: std_ajax_err => 
        `// Translators: A rolename appears this sentence. A rolename is something like "staff" or "beta tester".`
        cb? gettext("Error fetching list for role") + " '#{@rolename}'"

  # send ajax request to modify access
  # (add or remove them from the list)
  # `action` can be 'allow' or 'revoke'
  # `cb` is called with cb(error, data)
  modify_member_access: (unique_student_identifier, action, cb) ->
    $.ajax
      dataType: 'json'
      url: @modify_endpoint
      data:
        unique_student_identifier: unique_student_identifier
        rolename: @rolename
        action: action
      success: (data) => @member_response data
      error: std_ajax_err => cb? gettext "Error changing user's permissions."

  member_response: (data) ->
    @clear_errors()
    @clear_input()
    if data.userDoesNotExist
      msg = gettext("Could not find a user with username or email address '<%= identifier %>'.")
      @show_errors _.template(msg, {identifier: data.unique_student_identifier})
    else if data.inactiveUser
      msg = gettext("Error: User '<%= username %>' has not yet activated their account. Users must create and activate their accounts before they can be assigned a role.")
      @show_errors _.template(msg, {username: data.unique_student_identifier})
    else if data.removingSelfAsInstructor
      @show_errors gettext "Error: You cannot remove yourself from the Instructor group!"
    else
      @reload_list()


class BetaTesterBulkAddition
  constructor: (@$container) ->
    # gather elements
    @$identifier_input       = @$container.find("textarea[name='student-ids-for-beta']")
    @$btn_beta_testers       = @$container.find("input[name='beta-testers']")
    @$checkbox_autoenroll    = @$container.find("input[name='auto-enroll']")
    @$checkbox_emailstudents = @$container.find("input[name='email-students-beta']")
    @$task_response          = @$container.find(".request-response")
    @$request_response_error = @$container.find(".request-response-error")

    # click handlers
    @$btn_beta_testers.click (event) =>
      emailStudents = @$checkbox_emailstudents.is(':checked')
      autoEnroll = @$checkbox_autoenroll.is(':checked')
      send_data = 
        action: $(event.target).data('action')  # 'add' or 'remove'
        identifiers: @$identifier_input.val()
        email_students: emailStudents
        auto_enroll: autoEnroll

      $.ajax
        dataType: 'json'
        type: 'POST'
        url: @$btn_beta_testers.data 'endpoint'
        data: send_data
        success: (data) => @display_response data
        error: std_ajax_err => @fail_with_error gettext "Error adding/removing users as beta testers."

  # clear the input text field
  clear_input: ->
    @$identifier_input.val ''
    # default for the checkboxes should be checked
    @$checkbox_emailstudents.attr('checked', true)
    @$checkbox_autoenroll.attr('checked', true)

  fail_with_error: (msg) ->
    console.warn msg
    @clear_input()
    @$task_response.empty()
    @$request_response_error.empty()
    @$request_response_error.text msg

  display_response: (data_from_server) ->
    @clear_input()
    @$task_response.empty()
    @$request_response_error.empty()
    errors = []
    successes = []
    no_users = []
    for student_results in data_from_server.results
      if student_results.userDoesNotExist
        no_users.push student_results
      else if student_results.error
        errors.push student_results
      else
        successes.push student_results

    render_list = (label, ids) =>
      task_res_section = $ '<div/>', class: 'request-res-section'
      task_res_section.append $ '<h3/>', text: label
      ids_list = $ '<ul/>'
      task_res_section.append ids_list

      for identifier in ids
        ids_list.append $ '<li/>', text: identifier

      @$task_response.append task_res_section

    if successes.length and data_from_server.action is 'add'
      `// Translators: A list of users appears after this sentence`
      render_list gettext("These users were successfully added as beta testers:"), (sr.identifier for sr in successes)

    if successes.length and data_from_server.action is 'remove'
      `// Translators: A list of users appears after this sentence`
      render_list gettext("These users were successfully removed as beta testers:"), (sr.identifier for sr in successes)

    if errors.length and data_from_server.action is 'add'
      `// Translators: A list of users appears after this sentence`
      render_list gettext("These users were not added as beta testers:"), (sr.identifier for sr in errors)

    if errors.length and data_from_server.action is 'remove'
      `// Translators: A list of users appears after this sentence`
      render_list gettext("These users were not removed as beta testers:"), (sr.identifier for sr in errors)

    if no_users.length
      no_users.push $ gettext("Users must create and activate their account before they can be promoted to beta tester.")
      `// Translators: A list of identifiers (which are email addresses and/or usernames) appears after this sentence`
      render_list gettext("Could not find users associated with the following identifiers:"), (sr.identifier for sr in no_users)

# Wrapper for the batch enrollment subsection.
# This object handles buttons, success and failure reporting,
# and server communication.
class BatchEnrollment
  constructor: (@$container) ->
    # gather elements
    @$identifier_input       = @$container.find("textarea[name='student-ids']")
    @$enrollment_button      = @$container.find(".enrollment-button")
    @$checkbox_autoenroll    = @$container.find("input[name='auto-enroll']")
    @$checkbox_emailstudents = @$container.find("input[name='email-students']")
    @$task_response          = @$container.find(".request-response")
    @$request_response_error = @$container.find(".request-response-error")

    # attach click handler for enrollment buttons
    @$enrollment_button.click (event) =>
      emailStudents = @$checkbox_emailstudents.is(':checked')
      send_data =
        action: $(event.target).data('action') # 'enroll' or 'unenroll'
        identifiers: @$identifier_input.val()
        auto_enroll: @$checkbox_autoenroll.is(':checked')
        email_students: emailStudents

      $.ajax
        dataType: 'json'
        type: 'POST'
        url: $(event.target).data 'endpoint'
        data: send_data
        success: (data) => @display_response data
        error: std_ajax_err => @fail_with_error gettext "Error enrolling/unenrolling users."


  # clear the input text field
  clear_input: ->
    @$identifier_input.val ''
    # default for the checkboxes should be checked
    @$checkbox_emailstudents.attr('checked', true)
    @$checkbox_autoenroll.attr('checked', true)

  fail_with_error: (msg) ->
    console.warn msg
    @clear_input()
    @$task_response.empty()
    @$request_response_error.empty()
    @$request_response_error.text msg

  display_response: (data_from_server) ->
    @clear_input()
    @$task_response.empty()
    @$request_response_error.empty()

    # these results arrays contain student_results
    # only populated arrays will be rendered
    #
    # invalid identifiers
    invalid_identifier = []
    # students for which there was an error during the action
    errors = []
    # students who are now enrolled in the course
    enrolled = []
    # students who are now allowed to enroll in the course
    allowed = []
    # students who will be autoenrolled on registration
    autoenrolled = []
    # students who are now not enrolled in the course
    notenrolled = []
    # students who were not enrolled or allowed prior to unenroll action
    notunenrolled = []

    # categorize student results into the above arrays.
    for student_results in data_from_server.results
      # for a successful action.
      # student_results is of the form {
      #   "identifier": "jd405@edx.org",
      #   "before": {
      #     "enrollment": true,
      #     "auto_enroll": false,
      #     "user": true,
      #     "allowed": false
      #   }
      #   "after": {
      #     "enrollment": true,
      #     "auto_enroll": false,
      #     "user": true,
      #     "allowed": false
      #   },
      # }
      #
      # for an action error.
      # student_results is of the form {
      #   'identifier': identifier,
      #   # then one of:
      #   'error': True,
      #   'invalidIdentifier': True  # if identifier can't find a valid User object and doesn't pass validate_email
      # }

      if student_results.invalidIdentifier
        invalid_identifier.push student_results

      else if student_results.error
        errors.push student_results

      else if student_results.after.enrollment
        enrolled.push student_results

      else if student_results.after.allowed
        if student_results.after.auto_enroll
          autoenrolled.push student_results
        else
          allowed.push student_results

      # The instructor is trying to unenroll someone who is not enrolled or allowed to enroll; non-sensical action.
      else if data_from_server.action is 'unenroll' and not (student_results.before.enrollment) and not (student_results.before.allowed)
        notunenrolled.push student_results

      else if not student_results.after.enrollment
        notenrolled.push student_results

      else
        console.warn 'student results not reported to user'
        console.warn student_results

    # render populated result arrays
    render_list = (label, ids) =>
      task_res_section = $ '<div/>', class: 'request-res-section'
      task_res_section.append $ '<h3/>', text: label
      ids_list = $ '<ul/>'
      task_res_section.append ids_list

      for identifier in ids
        ids_list.append $ '<li/>', text: identifier

      @$task_response.append task_res_section

    if invalid_identifier.length
      render_list gettext("The following email addresses and/or usernames are invalid:"), (sr.identifier for sr in invalid_identifier)

    if errors.length
      errors_label = do ->
        if data_from_server.action is 'enroll'
          "There was an error enrolling:"
        else if data_from_server.action is 'unenroll'
          "There was an error unenrolling:"
        else
          console.warn "unknown action from server '#{data_from_server.action}'"
          "There was an error processing:"

      for student_results in errors
        render_list errors_label, (sr.identifier for sr in errors)

    if enrolled.length and emailStudents
      render_list gettext("Successfully enrolled and sent email to the following users:"), (sr.identifier for sr in enrolled)

    if enrolled.length and not emailStudents
      `// Translators: A list of users appears after this sentence`
      render_list gettext("Successfully enrolled the following users:"), (sr.identifier for sr in enrolled)

    # Student hasn't registered so we allow them to enroll
    if allowed.length and emailStudents
      `// Translators: A list of users appears after this sentence`
      render_list gettext("Successfully sent enrollment emails to the following users. They will be allowed to enroll once they register:"),
        (sr.identifier for sr in allowed)

    # Student hasn't registered so we allow them to enroll
    if allowed.length and not emailStudents
      `// Translators: A list of users appears after this sentence`
      render_list gettext("These users will be allowed to enroll once they register:"),
        (sr.identifier for sr in allowed)

    # Student hasn't registered so we allow them to enroll with autoenroll
    if autoenrolled.length and emailStudents
      `// Translators: A list of users appears after this sentence`
      render_list gettext("Successfully sent enrollment emails to the following users. They will be enrolled once they register:"),
        (sr.identifier for sr in autoenrolled)

    # Student hasn't registered so we allow them to enroll with autoenroll
    if autoenrolled.length and not emailStudents
      `// Translators: A list of users appears after this sentence`
      render_list gettext("These users will be enrolled once they register:"),
        (sr.identifier for sr in autoenrolled)

    if notenrolled.length and emailStudents
      `// Translators: A list of users appears after this sentence`
      render_list gettext("Emails successfully sent. The following users are no longer enrolled in the course:"),
        (sr.identifier for sr in notenrolled)

    if notenrolled.length and not emailStudents
      `// Translators: A list of users appears after this sentence`
      render_list gettext("The following users are no longer enrolled in the course:"),
        (sr.identifier for sr in notenrolled)

    if notunenrolled.length
      `// Translators: A list of users appears after this sentence. This situation arises when a staff member tries to unenroll a user who is not currently enrolled in this course.`
      render_list gettext("These users were not affiliated with the course so could not be unenrolled:"),
        (sr.identifier for sr in notunenrolled)

# Wrapper for auth list subsection.
# manages a list of users who have special access.
# these could be instructors, staff, beta users, or forum roles.
# uses slickgrid to display list.
class AuthList
  # rolename is one of ['instructor', 'staff'] for instructor_staff endpoints
  # rolename is the name of Role for forums for the forum endpoints
  constructor: (@$container, @rolename) ->
    # gather elements
    @$display_table          = @$container.find('.auth-list-table')
    @$request_response_error = @$container.find('.request-response-error')
    @$add_section            = @$container.find('.auth-list-add')
    @$allow_field             = @$add_section.find("input[name='email']")
    @$allow_button            = @$add_section.find("input[name='allow']")

    # attach click handler
    @$allow_button.click =>
      @access_change @$allow_field.val(), 'allow', => @reload_auth_list()
      @$allow_field.val ''

    @reload_auth_list()

  # fetch and display list of users who match criteria
  reload_auth_list: ->
    # helper function to display server data in the list
    load_auth_list = (data) =>
      # clear existing data
      @$request_response_error.empty()
      @$display_table.empty()

      # setup slickgrid
      options =
        enableCellNavigation: true
        enableColumnReorder: false
        # autoHeight: true
        forceFitColumns: true

      # this is a hack to put a button/link in a slick grid cell
      # if you change columns, then you must update
      # WHICH_CELL_IS_REVOKE to have the index
      # of the revoke column (left to right).
      WHICH_CELL_IS_REVOKE = 3
      columns = [
        id: 'username'
        field: 'username'
        name: 'Username'
      ,
        id: 'email'
        field: 'email'
        name: 'Email'
      ,
        id: 'first_name'
        field: 'first_name'
        name: 'First Name'
      ,
      #   id: 'last_name'
      #   field: 'last_name'
      #   name: 'Last Name'
      # ,
        id: 'revoke'
        field: 'revoke'
        name: 'Revoke'
        formatter: (row, cell, value, columnDef, dataContext) ->
          "<span class='revoke-link'>Revoke Access</span>"
      ]

      table_data = data[@rolename]

      $table_placeholder = $ '<div/>', class: 'slickgrid'
      @$display_table.append $table_placeholder
      grid = new Slick.Grid($table_placeholder, table_data, columns, options)

      # click handler part of the revoke button/link hack.
      grid.onClick.subscribe (e, args) =>
        item = args.grid.getDataItem(args.row)
        if args.cell is WHICH_CELL_IS_REVOKE
          @access_change item.email, 'revoke', => @reload_auth_list()

    # fetch data from the endpoint
    # the endpoint comes from data-endpoint of the table
    $.ajax
      dataType: 'json'
      url: @$display_table.data 'endpoint'
      data: rolename: @rolename
      success: load_auth_list
      error: std_ajax_err => @$request_response_error.text "Error fetching list for '#{@rolename}'"


  # slickgrid's layout collapses when rendered
  # in an invisible div. use this method to reload
  # the AuthList widget
  refresh: ->
    @$display_table.empty()
    @reload_auth_list()

  # update the access of a user.
  # (add or remove them from the list)
  # action should be one of ['allow', 'revoke']
  access_change: (email, action, cb) ->
    $.ajax
      dataType: 'json'
      url: @$add_section.data 'endpoint'
      data:
        email: email
        rolename: @rolename
        action: action
      success: (data) -> cb?(data)
      error: std_ajax_err => @$request_response_error.text gettext "Error changing user's permissions."

class EmailSelectors
  constructor: (@$container, @$section, params={}) ->
    params = _.defaults params,
      label : $container.data 'label'

    template_html = $("#email-list-widget-template").html()
    @$container.html Mustache.render template_html, params
    @cur_column = 0
    @$table = $( "#queryTableBody" )
    @labelArray = ($container.data 'selections').split '<>'
    @$list_selector = @$container.find 'select.single-email-selector'
    # populate selectors
    @$list_selector.empty()
    @$list_endpoint = $container.data 'list-endpoint'
    @$rolename = $container.data 'rolename'
    @$list_selector.append $ '<option/>'
    if this.$container.attr('data-label')=='Select Section'
      @load_list()
    else if this.$container.attr('data-label')=='Select Problem'
      @load_list()
    else
      for label in @labelArray
          @$list_selector.append $ '<option/>',
            text: label

    @parent = @$container.parent()
    @idx = @$container.prevAll().length
    @c = @$section.find('.section_specific').get(0).children[0]

    @$list_selector.change =>
      $opt = @$list_selector.children('option:selected')
      return unless $opt.length > 0

      @c = @parent.children()[@idx+1]
      if this.$container.attr('data-label')=="Select a Type"
        @chosen_class = $opt.text().trim()
        if (@chosen_class == "Section")
          @$section.find('.problem_specific').removeClass("active")
          @$section.find('.section_specific').addClass("active")
        else if (@chosen_class == "Problem")
          @$section.find('.section_specific').removeClass("active")
          @$section.find('.problem_specific').addClass("active")

  get_list: (cb)->
    $.ajax
      dataType: 'json'
      url: @$list_endpoint
      data: rolename: 'instructor'
      success: (data) => cb? null, data['data']
      error: std_ajax_err =>
        cb? gettext("Error fetching problem or section data")

  # load section/problem data
  load_list: ->
    @get_list (error, section_list) =>
      # abort on error
      return @show_errors error unless error is null
      _.each section_list, (section) =>
        @add_row( section, "section")
        _.each section.sub, (subsection) =>
          @add_row(subsection , "subsection")

  add_row: (node, useClass) ->
    @idArr = [node.block_type, node.block_id]
    @idSt = @idArr.join("/")
    @toDisplay = node.display_name
    if node.parents
      @toDisplay = [node.parents,@toDisplay].join("<>")
    #indenting subsections for readability
    if useClass=="subsection"
      @toDisplay = "---"+@toDisplay
    if @toDisplay.length>50
      #displaying the last n characters
      @toDisplay = "..."+@toDisplay.substring(@toDisplay.length-60, @toDisplay.length)
    @$list_selector.append $ '<option/>',
            text: @toDisplay
            class: useClass
            id : @idSt

  set_cell: (text, colNumber,cellid) ->
    rows = $("#queryTableBody")[0].rows
    cell = rows[rows.length-1].children[colNumber]
    if cell
      cell.innerHTML = text
      if cellid !=""
        cell.id = cellid

class EmailWidget
  constructor:  (@email_lists, @$section, @$email_list_containers)  ->
    @$query_endpoint = $(".email-lists-management").data('query-endpoint')
    @$total_endpoint = $(".email-lists-management").data('total-endpoint')
    @$temp_queries_endpoint = $(".email-lists-management").data('temp-queries-endpoint')
    @$delete_saved_endpoint = $(".email-lists-management").data('delete-saved-endpoint')
    @$delete_temp_endpoint = $(".email-lists-management").data('delete-temp-endpoint')
    @$delete_bulk_temp_endpoint = $(".email-lists-management").data('delete-bulk-temp-endpoint')
    for email_list in @email_lists
      email_list.$container.addClass 'active'

    @$get_est_btn = @$section.find("input[name='getest']'")
    @$get_est_btn.click () =>
      @reload_estimated()

    @$startover_btn = @$section.find("input[name='startover']'")
    @$startover_btn.click () =>
      @delete_temporary()
      $("#queryTableBody tr").remove()
      @reload_estimated()

    @$save_query_btn = @$section.find("input[name='savequery']'")
    @$save_query_btn.click () =>
      @send_save_query()

    @$email_csv_btn = @$section.find("input[name='getcsv']'")
    @$email_csv_btn.click () =>
      b = []
      tab = $("#queryTableBody")
      rows = tab.find("tr")
      _.each rows, (row) =>
        b.push(row.getAttribute('query'))

      send_data = b.join(',')
      url = @$email_csv_btn.data 'endpoint'
      # handle csv special case
      # redirect the document to the csv file.
      url += '/csv'
      url += "?rolename=instructor"
      url += "&existing="+ encodeURIComponent(send_data)
      location.href = url

    @load_saved_queries()
    @load_saved_temp_queries()

    #poll for query status every 15 seconds
    POLL_INTERVAL = 1000 * 15  # 15 seconds in ms
    @poller = new window.InstructorDashboard.util.IntervalManager(
      POLL_INTERVAL, => @load_saved_temp_queries()
    )
    @poller.start()

    $('#addQuery').click =>
        selected = @$email_list_containers.find('select.single-email-selector').children('option:selected')
        #check to see if stuff has been filled out
        if selected[1].text=="Section"
          @arr = [{'text':selected[0].text, 'id':selected[0].id},
                  {'text':selected[1].text, 'id':selected[1].id},
                  {'text':selected[4].text, 'id':selected[4].id},
                  {'text':selected[5].text, 'id':selected[5].id}]
          @arr_text = [selected[0].text, selected[1].text, selected[4].text, selected[5].text]

        else
          @arr = [{'text':selected[0].text, 'id':selected[0].id},
                  {'text':selected[1].text, 'id':selected[1].id},
                  {'text':selected[2].text, 'id':selected[2].id},
                  {'text':selected[3].text, 'id':selected[3].id}]
          @arr_text = [selected[0].text, selected[1].text, selected[2].text, selected[3].text]

        for thing in @arr
          if thing['text']==""
            $("#incompleteMessage")[0].innerHTML = "Query is incomplete. Please make all the selections."
            return

        $("#incompleteMessage")[0].innerHTML = ""
        @chosen = selected[0].text
        @tr = @start_row(@chosen.toLowerCase(), @arr,"", $( "#queryTableBody" ))
        @use_query_endpoint =@$query_endpoint+"/"+@arr_text.slice(0,2).join("/")+"/"+@arr[2].id
        @filtering = @arr[3].text
        @entityName = @arr[2].text
        @reload_students(@tr)
        @$email_list_containers.find('select.single-email-selector').prop('selectedIndex',0);
        $(".problem_specific").removeClass('active')
        $(".section_specific").removeClass('active')

  get_saved_temp_queries: (cb)->
    $.ajax
      dataType: 'json'
      url: @$temp_queries_endpoint
      data: rolename: 'instructor'
      success: (data) => cb? null, data
      error: std_ajax_err =>
        cb? gettext("Error getting saved temp queries")

  #get a user's in-progress queries and load them into active queries
  load_saved_temp_queries: ->
    @get_saved_temp_queries (error, data) =>
      # abort on error
      return @show_errors error unless error is null
      $("#queryTableBody tr").remove()
      queries = data['queries']
      # use _.each instead of 'for' so that member
      # is bound in the button callback.
      _.each queries, (query) =>
        query_id = query['id']
        block_id = query['block_id']
        block_type = query['block_type']
        state_key = block_type+"/" +block_id
        display_name = query['display_name']
        display_entity = {'text':display_name, 'id':state_key}
        filter_on = {'text':query['filter_on']}
        inclusion = {'text':query['inclusion']}
        done = query['done']
        type = {'text':query['type']}
        arr = [inclusion,type, display_entity, filter_on, done]
        @tr = @start_row(inclusion['text'].toLowerCase(),arr,{'class':["working"],'query':query_id},  $( "#queryTableBody" ))
        @check_done()


  get_saved_queries: (cb)->
    $.ajax
      dataType: 'json'
      url: $("#savedQueriesTable").data 'endpoint'
      data: rolename: 'instructor'
      success: (data) => cb? null, data
      error: std_ajax_err =>
        cb? gettext("Error getting saved queries")

  #get a user's saved queries and load them into saved queries
  load_saved_queries: ->
    $("#savedQueriesTable tr").remove()
    $("#invisibleQueriesStorage tr").remove()
    @get_saved_queries (error, data) =>
      # abort on error
      return @show_errors error unless error is null
      queries = data['queries']
      groups = new Set()
      _.each queries, (query) =>
        block_id = query['block_id']
        block_type = query['block_type']
        state_key = block_type+"/" +block_id
        display_name = query['display_name']
        display_entity = {'text':display_name, 'id':state_key}
        filter_on = {'text':query['filter_on']}
        inclusion = {'text':query['inclusion']}
        created = query['created']
        type = {'text':query['type']}
        arr = [inclusion,type, display_entity, filter_on]
        invisibleTable = $("#invisibleQueriesStorage")
        @tr = @start_row(inclusion['text'],arr,{'class':["saved"+query.group]}, invisibleTable)
        @tr[0].setAttribute('created',created)
        groups.add(query.group)
      group_arr = []
      iter = groups.values()
      val = iter.next()
      while (val['done']==false)
        group_arr.push(val['value'])
        val = iter.next()
      group_arr.sort((a, b)=>return b-a)
      for group in group_arr
        lookup = ".saved"+group
        saved_qs = $(lookup)
        types = []
        names = []
        time = ""
        for q in saved_qs
          cells = q.children
          types.push(cells[0].innerText)
          names.push(cells[2].innerText)
          time = q.getAttribute('created')
        display_st = ""
        for i in [0..types.length-1]
          display_st += types[i]
          display_st +=" "
          display_st += names[i]+" "
        arr = [{"text":time}, {"text":display_st}]
        @start_saved_row("and",arr, group, $( "#savedQueriesTable" ) )

  #if each individual query is processed, allow the user to download the csv and save the query
  check_done: ->
    #check if all other queries have returned, if so can get total csv
    b = []
    tab = $("#queryTableBody")
    rows = tab.find("tr")
    _.each rows, (row) =>
      b.push(row.getAttribute('query'))
    allGood = true
    _.each b, (status) =>
      if status=="working"
        allGood = false
    if allGood
      @$save_query_btn.removeClass("disabled")
      @$email_csv_btn.removeClass("disabled")
      @$email_csv_btn[0].value = "Download CSV"

  #deletes an active query from the table and the db
  delete_temporary:->
    queriesToDelete = []
    _.each $("#queryTableBody tr"), (row) =>
      if row.hasAttribute('query')
         queryToDelete = row.getAttribute('query')
         queriesToDelete.push(queryToDelete)
    @delete_bulk_temp_query(queriesToDelete)
    $("#queryTableBody tr").remove()

  #adds a row to saved queries
  start_saved_row:(color, arr, id, table) ->
    #find which row to insert in
    rows = table[0].children
    row = table[0].insertRow(rows);
    row.setAttribute("groupQuery", id)
    for num in [0..1]
      cell = row.insertCell(num)
      item = arr[num]
      cell.innerHTML = item['text']
      if item.hasOwnProperty('id')
        cell.id = item['id']
    $load_btn = $ _.template('<div class="loadQuery"><i class="icon-upload"></i> <%= label %></div>', {label: "Load"})
    $load_btn.click =>
      @delete_temporary()
      $("#queryTableBody tr").remove()
      targ = event.target
      while (!targ.classList.contains('loadQuery'))
        targ = targ.parentNode
      curRow = targ.parentNode.parentNode
      groupedQueryId = curRow.getAttribute('groupQuery')
      @$email_csv_btn[0].value = "Aggregating Queries"
      $("#incompleteMessage")[0].innerHTML = ""
      rowsToAdd = $(".saved"+groupedQueryId)
      for row in rowsToAdd
        cells = row.children
        @arr = [{'text':cells[0].innerText},
                {'text':cells[1].innerText},
                {'text':cells[2].innerText, 'id':cells[2].id},
                {'text':cells[3].innerText}]

        @arr_text = [cells[0].innerText, cells[1].innerText, cells[2].innerText, cells[3].innerText]
        @tr = @start_row(cells[0].innerText.toLowerCase(), @arr,"", $( "#queryTableBody" ))
        #todo:this feels too hacky. suggestions?
        @use_query_endpoint =@$query_endpoint+"/"+@arr_text.slice(0,2).join("/")+"/"+@arr[2].id
        @filtering = @arr[3].text
        @entityName = @arr[2].text
        @reload_students(@tr)
        @$email_list_containers.find('select.single-email-selector').prop('selectedIndex',0);
        $(".problem_specific").removeClass('active')
        $(".section_specific").removeClass('active')
    $td = $ '<td>'
    $td.append $load_btn
    row.appendChild $td[0]
    $delete_btn = $ _.template('<div class="deleteSaved"><i class="icon-remove-sign"></i> <%= label %></div>', {label: "Delete"})
    $delete_btn.click =>
      targ = event.target
      while (!targ.classList.contains('deleteSaved'))
        targ = targ.parentNode
      curRow = targ.parentNode.parentNode
      curRow.remove()
      queryToDelete = curRow.getAttribute('groupquery')
      @delete_saved_query(queryToDelete)
    $td = $ '<td>'
    $td.append $delete_btn
    row.appendChild $td[0]
    return $(row)

  get_students: (cb)->
    tab = $("#queryTableBody")
    b = []
    rows = tab.find("tr")
    _.each rows, (row) =>
      type = row.classList[0]
      problems = []
      children = row.children
      _.each children, (child) =>
        id = child.id
        html = child.innerHTML
        problems.push({"id":id, "text":html})
      problems = problems.slice(0,-1)
      b.push([type, problems])
    send_data =
      filter: @filtering
      entityName: @entityName
    $.ajax
      dataType: 'json'
      url: @use_query_endpoint
      data: send_data
      success: (data) => cb? null, data
      error: std_ajax_err =>
        cb? gettext("Error getting students")

  #make a single query to the backend. doesn't wait for query completion as that can take awhile
  reload_students: (tr) ->
      @$save_query_btn.addClass("disabled")
      @$email_csv_btn.addClass("disabled")
      @$email_csv_btn[0].value = "Aggregating Queries"
      tr.addClass("working")
      @get_students (error, students) =>
        if error
           $broken_icon = $ _.template('<div class="done"><i class="icon-warning-sign"></i> <%= label %></div>',
             {label: "Sorry, we're having a problem with this query. Please delete this row and try again."})
           tr.children()[4].innerHTML = $broken_icon[0].outerHTML
        return @show_errors error unless error is null

  #we don't care if these calls succeed or not so no wrapped callback
  delete_temp_query: (queryId)->
    send_url = @$delete_temp_endpoint+"/"+queryId
    $.ajax
      dataType: 'json'
      url: send_url

  delete_bulk_temp_query: (queryIds)->
    send_url = @$delete_bulk_temp_endpoint
    send_data =
      existing: queryIds.join(',')
    $.ajax
      dataType: 'json'
      url: send_url
      data: send_data

  delete_saved_query: (queryId)->
    send_url = @$delete_saved_endpoint+"/"+queryId
    $.ajax
      dataType: 'json'
      url: send_url

  #adds a row to active queries
  start_row:(color, arr, rowIdClass, table) ->
    #find which row to insert in
    idx =0
    orIdx = 0
    andIdx = 0
    notIdx = 0
    useIdx = 0
    rows = table[0].children
    #figuring out where to place the new row
    #we want the group order to be and, or, not
    for curRow in rows
      idx +=1
      if curRow.classList.contains("or")
        orIdx = idx
      if curRow.classList.contains("and")
        andIdx = idx
      if curRow.classList.contains("not")
        notIdx = idx
      if curRow.classList.contains(color)
        useIdx = idx
    if color=="or" and useIdx==0
      useIdx =Math.max(notIdx, andIdx)
    if color=="not" and useIdx==0
      useIdx =andIdx
    row = table[0].insertRow(useIdx);
    if rowIdClass.hasOwnProperty('id')
      row.id = rowIdClass['id']
    if rowIdClass.hasOwnProperty('query')
      row.setAttribute('query',rowIdClass['query'])

    row.classList.add(color.toLowerCase())
    if rowIdClass.hasOwnProperty('class')
      _.each rowIdClass['class'], (addingClass) =>
         row.classList.add(addingClass.toLowerCase())
    for num in [0..3]
      cell = row.insertCell(num)
      item = arr[num]
      cell.innerHTML = item['text']
      if item.hasOwnProperty('id') and item['id'] !=""
        cell.id = item['id']
    progressCell = row.insertCell(4)
    $progress_icon = $ _.template('<div class="Working"><i class="icon-spinner icon-spin"></i> <%= label %></div>', {label: "Working"})
    $done_icon = $ _.template('<div class="done"><i class="icon-check"></i> <%= label %></div>', {label: "Done"})
    $broken_icon = $ _.template('<div class="done"><i class="icon-warning-sign"></i> <%= label %></div>',
      {label: "Sorry, we're having a problem with this query. Please delete this row and try again."})
    if arr.length==4
      progressCell.innerHTML = $progress_icon[0].outerHTML
    else
      if arr[4]==null
        progressCell.innerHTML = $broken_icon[0].outerHTML
      else if arr[4]==true
        progressCell.innerHTML = $done_icon[0].outerHTML
        row.classList.remove('working')
      else
        progressCell.innerHTML = $progress_icon[0].outerHTML
    $remove_btn = $ _.template('<div class="remove"><i class="icon-remove-sign"></i> <%= label %></div>', {label: "Remove"})
    $remove_btn.click =>
      targ = event.target
      while (!targ.classList.contains('remove'))
        targ = targ.parentNode
      curRow = targ.parentNode.parentNode
      curRow.remove()
      if curRow.hasAttribute('query')
        queryToDelete = curRow.getAttribute('query')
        @delete_temp_query(queryToDelete)
      @check_done()
    $td = $ '<td>'
    $td.append $remove_btn
    row.appendChild $td[0]
    return $(row)

  save_query: (cb)->
    b = []
    tab = $("#queryTableBody")
    rows = tab.find("tr")
    _.each rows, (row) =>
      b.push(row.getAttribute('query'))
    send_data =
      existing: b.join(',')
    $.ajax
      dataType: 'json'
      url: @$save_query_btn.data 'endpoint'
      data: send_data
      success: (data) => cb? null, data
      error: std_ajax_err =>
        cb? gettext("Error saving query")

  #save queries in active queries
  send_save_query: ->
    @save_query (error, students) =>
      return @show_errors error unless error is null
      @load_saved_queries()

  get_estimated: (cb)->
      b = []
      tab = $("#queryTableBody")
      rows = tab.find("tr")
      _.each rows, (row) =>
        b.push(row.getAttribute('query'))
      send_data =
        existing: b.join(',')
      $.ajax
        dataType: 'json'
        url: @$total_endpoint
        data: send_data
        success: (data) => cb? null, data
        error: std_ajax_err =>
          cb? gettext("Error getting estimated")

  #estimate the students selected
  reload_estimated: ->
      $("#estimated")[0].innerHTML= "Calculating"
      @get_estimated (error, students) =>
        students_list = students['data']
        query_id = students['query_id']
        # abort on error
        return @show_errors error unless error is null
        $number_students = students_list.length
        $("#estimated")[0].innerHTML="approx " + $number_students+" students selected"
  # set error display
  show_errors: (msg) -> @$error_section?.text msg

# Membership Section
class Membership
  # enable subsections.
  constructor: (@$section) ->
    # attach self to html
    # so that instructor_dashboard.coffee can find this object
    # to call event handlers like 'onClickTitle'
    @$section.data 'wrapper', @

    # isolate # initialize BatchEnrollment subsection
    plantTimeout 0, => new BatchEnrollment @$section.find '.batch-enrollment'
    
    # initialize BetaTesterBulkAddition subsection
    plantTimeout 0, => new BetaTesterBulkAddition @$section.find '.batch-beta-testers'

    # gather elements
    @$list_selector = @$section.find 'select#member-lists-selector'
    @$auth_list_containers = @$section.find '.auth-list-container'
    @$auth_list_errors = @$section.find '.member-lists-management .request-response-error'

    # initialize & store AuthList subsections
    # one for each .auth-list-container in the section.
    @auth_lists = _.map (@$auth_list_containers), (auth_list_container) =>
      rolename = $(auth_list_container).data 'rolename'
      new AuthListWidget $(auth_list_container), rolename, @$auth_list_errors

    #initialize email widget selectors
    @$email_list_containers = @$section.find '.email-list-container'
    @email_lists = _.map (@$email_list_containers), (email_list_container) =>
      new EmailSelectors $(email_list_container), @$section

    #initialize email widget
    new EmailWidget @email_lists, @$section, @$email_list_containers
    # populate selector
    @$list_selector.empty()
    for auth_list in @auth_lists
      @$list_selector.append $ '<option/>',
        text: auth_list.$container.data 'display-name'
        data:
          auth_list: auth_list
    if @auth_lists.length is 0
      @$list_selector.hide()

    @$list_selector.change =>
      $opt = @$list_selector.children('option:selected')
      return unless $opt.length > 0
      for auth_list in @auth_lists
        auth_list.$container.removeClass 'active'
      auth_list = $opt.data('auth_list')
      auth_list.$container.addClass 'active'
      auth_list.re_view()
    # one-time first selection of top list.
    @$list_selector.change()



  # handler for when the section title is clicked.
  onClickTitle: ->

# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  Membership: Membership

