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

class EmailWidget
  constructor: (@$container, @$section, params={}) ->
    params = _.defaults params,
      label : $container.data 'label'

    $containers = @$section.find '.email-lists-management'
    template_html = $("#email-list-widget-template").html()
    @$container.html Mustache.render template_html, params
    @cur_column = 0
    @$table = $( "#emailTable" )

    @labelArray = ($container.data 'selections').split '<>'
    @$list_selector = @$container.find 'select.single-email-selector'
    # populate selector
    @$list_selector.empty()
    @$list_endpoint = $container.data 'list-endpoint'
    @$rolename = $container.data 'rolename'
    @$list_selector.append $ '<option/>',
          text: ""


    if this.$container.attr('data-label')=='Select Section'
      @reload_list()
    else if this.$container.attr('data-label')=='Select Problem'
      @reload_list()
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

      #get the parent of this container
      #if (@idx != @parent.children().length-1)
      @c = @parent.children()[@idx+1]
      #if this.$container.attr('data-label') !="Inclusion"
          #@set_cell($opt.text().trim(),2, $opt.attr('id'))
      #else
      #if (@parent.attr('class')=="beginning_specific")
      if this.$container.attr('data-label')=="Select a Type"
        @chosen_class = $opt.text().trim()
        if (@chosen_class == "Section")
          @$section.find('.problem_specific').removeClass("active")
          @$section.find('.section_specific').addClass("active")
        else if (@chosen_class == "Problem")
          @$section.find('.section_specific').removeClass("active")
          @$section.find('.problem_specific').addClass("active")
          #@set_cell($opt.text().trim() ,1,"")
        #@sec_child = @$section.find('.beginning_specific').get(0).children[0]
        #@sec_child.classList.add("active")
        #@set_cell($opt.text().trim() ,3,"")
        #@reload_students()
      #@$list_selector.prop('selectedIndex',0);
        #@c .addClass 'active'


      #@$container.removeClass 'active'
    #@$list_selector.change()





    # send ajax request to list members
    # `cb` is called with cb(error, member_list)
  get_list: (cb)->
    $.ajax
      dataType: 'json'
      url: @$list_endpoint
      data: rolename: 'instructor'
      success: (data) => cb? null, data['data']
      error: std_ajax_err =>
        `// Translators: A rolename appears this sentence. A rolename is something like "staff" or "beta tester".`
        cb? gettext("Error fetching list for role") + " '#{@$rolename}'"

 # reload the list of members
  reload_list: ->
    # @clear_rows()
    @get_list (error, section_list) =>
      # abort on error
      return @show_errors error unless error is null
      # use _.each instead of 'for' so that member
      # is bound in the button callback.
      _.each section_list, (section) =>
        # if there are members, show the list
        #@add_row([section.display_name], "section")
        @add_row( section, "section")
        _.each section.sub, (subsection) =>
          @add_row(subsection , "subsection")


  add_row: (node, useClass) ->
    @idArr = [node.block_type, node.block_id]
    @idSt = @idArr.join("/")
    @toDisplay = node.display_name
    if node.parents
      @toDisplay = [node.parents,@toDisplay].join("<>")
    #hacky, but can't style select tags
    if useClass=="subsection"
      @toDisplay = "---"+@toDisplay
    if @toDisplay.length>50
      @toDisplay = "..."+@toDisplay.substring(@toDisplay.length-80, @toDisplay.length)
    @$list_selector.append $ '<option/>',
            text: @toDisplay
            class: useClass
            id : @idSt

  set_cell: (text, colNumber,cellid) ->
    $tbody = $( "#emailTable" )
    rows = $("#emailTable")[0].rows
    rowNumber = rows.length
    cell = rows[rows.length-1].children[colNumber]
    #rowNumber = $tbody[0].children.length

    #cell = $(["#emailtable",rowNumber, colNumber].join("-"))
    if cell
      cell.innerHTML = text
      if cellid !=""
        cell.id = cellid


    ###
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
    ###




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

    @$email_list_containers = @$section.find '.email-list-container'
    @email_lists = _.map (@$email_list_containers), (email_list_container) =>
      new EmailWidget $(email_list_container), @$section

    @$query_endpoint = $(".email-lists-management").data('query-endpoint')
    for email_list in @email_lists
      email_list.$container.addClass 'active'
    #@email_lists[0].$container.addClass 'active'
    @$email_csv_btn = @$section.find("input[name='getcsv']'")
    @$email_csv_btn.click (e) =>
      tab = $("#emailTable")
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

      url = @$email_csv_btn.data 'endpoint'
      # handle csv special case
      # redirect the document to the csv file.
      url += '/csv'
      url += "?rolename=instructor"
      url += "&queries="+ encodeURIComponent(JSON.stringify(b))
      location.href = url



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

      $('#addQuery').click =>
        selected = @$email_list_containers.find('select.single-email-selector').children('option:selected')
        #check to see if stuff has been filled out
        if selected[1].text=="Section"
          @arr = [selected[0], selected[1], selected[4], selected[5]]
          @arr_text = [selected[0].text, selected[1].text, selected[4].text, selected[5].text]
        else
          @arr = [selected[0], selected[1], selected[2], selected[3]]
          @arr_text = [selected[0].text, selected[1].text, selected[2].text, selected[3].text]

        for thing in @arr
          if thing.text==""
            $("#incompleteMessage")[0].innerHTML = "Query is incomplete. Please make all the selections."
            return
        $("#incompleteMessage")[0].innerHTML = ""
        @chosen = selected[0].text
        if @chosen !=""
          if @chosen=="AND"
            @start_row("and")
          else if @chosen=="NOT"
            @start_row("not")
          else
            @start_row("or")
        @use_query_endpoint =@$query_endpoint+"/"+@arr_text.slice(0,2).join("/")+"/"+@arr[2].id
        @filtering = @arr[3].text
        @existing = $("#estimated")[0].classList.toString()
        @reload_students()

        i = 0
        for item in @arr
          @set_cell(item.text,i, item.id )
          i= i+1
        @$email_list_containers.find('select.single-email-selector').prop('selectedIndex',0);
        $(".problem_specific").removeClass('active')
        $(".section_specific").removeClass('active')



    # one-time first selection of top list.
    @$list_selector.change()

  set_cell: (text, colNumber,cellid) ->
    $tbody = $( "#emailTable" )
    rows = $("#emailTable")[0].rows
    rowNumber = rows.length
    cell = rows[rows.length-1].children[colNumber]
    #rowNumber = $tbody[0].children.length

    #cell = $(["#emailtable",rowNumber, colNumber].join("-"))
    if cell
      cell.innerHTML = text
      if cellid !=""
        cell.id = cellid

  start_row: (color) ->
    $tbody = $( "#emailTable" )
    numRows = $tbody[0].children.length
    $tr = $ '<tr>',
       class: color
    @id = 0
    for num in [1..5]
      $td = $ '<td>',
        text : ""
        #id is not useful anymore because we can delete rows
        #id : ["emailtable",numRows+1, @id].join("-")
      #@id = @id+1
      $tr.append $td
    $tbody.append $tr
    $revoke_btn = $ _.template('<div class="remove"><i class="icon-remove-sign"></i> <%= label %></div>', {label: "Remove"}),
            class: 'remove'

    @set_cell($revoke_btn[0].outerHTML,4,"")
    $('.remove').click =>
      rowIdx = event.target.parentElement.parentElement.rowIndex
      totalRows =$("#emailTable")[0].rows.length
      #$("#emailTable")[0].deleteRow(rowIdx-1);
      event.target.parentNode.parentNode.remove()
      @reload_students()


  get_students: (cb)->
      tab = $("#emailTable")
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
        existing : @existing
      $.ajax
        dataType: 'json'
        url: @use_query_endpoint
        data: send_data
        success: (data) => cb? null, data
        error: std_ajax_err =>
          `// Translators: A rolename appears this sentence. A rolename is something like "staff" or "beta tester".`
          cb? gettext("Error fetching list for role") + " '#{@$rolename}'"

   # reload the list of members
    reload_students: (arr) ->
      # @clear_rows()
      $("#estimated")[0].innerHTML= "Calculating"
      @get_students (error, students) =>
        students_list = students['data']
        query_id = students['query_id']
        # abort on error
        return @show_errors error unless error is null
        # use _.each instead of 'for' so that member
        # is bound in the button callback.
        $number_students = students_list.length
        $("#estimated")[0].innerHTML= $number_students+" students selected"
        $("#estimated").addClass(query_id.toString())
  # handler for when the section title is clicked.
  onClickTitle: ->


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  Membership: Membership

