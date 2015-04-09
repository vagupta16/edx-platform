###
Analytics Section

imports from other modules.
wrap in (-> ... apply) to defer evaluation
such that the value can be defined later than this assignment (file load order).
###

plantTimeout = -> window.InstructorDashboard.util.plantTimeout.apply this, arguments
std_ajax_err = -> window.InstructorDashboard.util.std_ajax_err.apply this, arguments

# proxies to functions instead of specifying full path
get_avg = -> window.InstructorDashboard.util.Statistics.get_avg.apply this, arguments
get_stddev = -> window.InstructorDashboard.util.Statistics.get_stddev.apply this, arguments
get_zscore = -> window.InstructorDashboard.util.Statistics.get_zscore.apply this, arguments
update_rows_with_unique_ids = -> window.InstructorDashboard.util.SlickGridHelpers.update_rows_with_unique_ids.apply this, arguments
autogenerate_slickgrid_cols = -> window.InstructorDashboard.util.SlickGridHelpers.autogenerate_slickgrid_cols.apply this, arguments

class ProfileDistributionWidget
  constructor: ({@$container, @feature, @title, @endpoint}) ->
    # render template
    template_params =
      title: @title
      feature: @feature
      endpoint: @endpoint
    template_html = $("#profile-distribution-widget-template").text()
    @$container.html Mustache.render template_html, template_params

  reset_display: ->
      @$container.find('.display-errors').empty()
      @$container.find('.display-text').empty()
      @$container.find('.display-graph').empty()
      @$container.find('.display-table').empty()

  show_error: (msg) ->
    @$container.find('.display-errors').text msg

  # display data
  load: ->
    @reset_display()

    @get_profile_distributions @feature,
      error: std_ajax_err =>
          `// Translators: "Distribution" refers to a grade distribution. This error message appears when there is an error getting the data on grade distribution.`
          @show_error gettext("Error fetching distribution.")
      success: (data) =>
        feature_res = data.feature_results
        if feature_res.type is 'EASY_CHOICE'
          # display on SlickGrid
          options =
            enableCellNavigation: true
            enableColumnReorder: false
            forceFitColumns: true

          columns = [
            id: @feature
            field: @feature
            name: data.feature_display_names[@feature]
          ,
            id: 'count'
            field: 'count'
            name: 'Count'
          ]

          grid_data = _.map feature_res.data, (value, key) =>
            datapoint = {}
            datapoint[@feature] = feature_res.choices_display_names[key]
            datapoint['count'] = value
            datapoint

          table_placeholder = $ '<div/>', class: 'slickgrid'
          @$container.find('.display-table').append table_placeholder
          grid = new Slick.Grid(table_placeholder, grid_data, columns, options)
        else if feature_res.feature is 'year_of_birth'
          graph_placeholder = $ '<div/>', class: 'graph-placeholder'
          @$container.find('.display-graph').append graph_placeholder

          graph_data = _.map feature_res.data, (value, key) -> [parseInt(key), value]

          $.plot graph_placeholder, [
            data: graph_data
          ]
        else
          console.warn("unable to show distribution #{feature_res.type}")
          @show_error gettext('Unavailable metric display.')

  # fetch distribution data from server.
  # `handler` can be either a callback for success
  # or a mapping e.g. {success: ->, error: ->, complete: ->}
  get_profile_distributions: (feature, handler) ->
    settings =
      dataType: 'json'
      url: @endpoint
      data: feature: feature

    if typeof handler is 'function'
      _.extend settings, success: handler
    else
      _.extend settings, handler

    $.ajax settings


class StudentAnalyticsDataWidget
  constructor: ({@$container, @feature, @title, @endpoint}) ->
    @dataview = new Slick.Data.DataView({inlineFilters: true})
    @grid = null

    # resolve slickgrid formatter names to the
    # corresponding instance functions
    for attr in _.keys(@slickgrid_formatters)
      fn_name = @slickgrid_formatters[attr]
      @slickgrid_formatters[attr] = this[fn_name]

    # render template
    template_params =
      title: @title
      feature: @feature
      endpoint: @endpoint
    template_html = $("#student-analytics-data-widget-template").text()
    @$container.html Mustache.render template_html, template_params
    @$container.find('.problem-selector').on 'change', @on_select_date

  slickgrid_col_names:
    'total_video_activity': 'video activity'
    'unique_videos_watched': 'videos watched'
    'total_video_watch_time': 'min. watched'
    'num_forum_points': 'forum points'
    'num_forum_created': 'posts created'
    'num_attempts': 'num attempts'
    'num_unique_problems_tried': 'problems attempted'
    'cumulative_grade': 'cum grade'

  slickgrid_formatters:
    'total_video_activity': 'video_activity_formatter'
    'total_video_watch_time': 'watch_time_formatter'
    
  video_activity_formatter: (row, cell, value) =>
      avg = @calculated_stats.total_video_activity.avg
      stddev = @calculated_stats.total_video_activity.stddev
      if not avg or not stddev
        return value

      z_score = get_zscore(parseInt(value, 10), avg, stddev)
      if z_score < -0.5
        return '<div class="red dot"></div>'
      else if -0.5 <= z_score < 1
        return """
          <div class="silver dot"></div>
          <div class="silver dot"></div>
        """
      else if 1 <= z_score < 2
        return """
          <div class="green dot"></div>
          <div class="green dot"></div>
          <div class="green dot"></div>
        """
      else
        return """
          <div class="green dot"></div>
          <div class="green dot"></div>
          <div class="green dot"></div>
          <div class="green dot"></div>
        """

  watch_time_formatter: (row, cell, value) =>
      avg = @calculated_stats.total_video_watch_time.avg
      stddev = @calculated_stats.total_video_watch_time.stddev
      if not avg or not stddev
        return value

      z_score = get_zscore(parseInt(value, 10), avg, stddev)
      value_in_min = Math.round(value / 60.0)
      if z_score > 0.5
        return '<span class="highlight-text-green">' + value_in_min + '</span>'
      else if z_score < -0.5
        return '<span class="highlight-text-red">' + value_in_min + '</span>'
      else
        return value_in_min

  on_select_date: (e) =>
    time_span = $(e.currentTarget).val()
    @get_student_analytics_data
      data: {time_span: time_span}
      error: @error_handler
      success: @success_handler

  reset_display: ->
    @$container.find('.display-errors').empty()
    @$container.find('.display-text').empty()
    @$container.find('.display-graph').empty()
    @$container.find('.display-table').empty()

  show_error: (msg) ->
    @$container.find('.display-errors').text msg

  # display data
  load: ->
    @reset_display()
    @get_student_analytics_data
      error: @error_handler
      success: @success_handler

  error_handler: (response) =>
    text = if response.responseText? then response.responseText else gettext("Error fetching student data for given time period")
    @show_error text

  success_handler: (response) =>
    @reset_display()
    @render_last_updated(response.last_updated)
    @render_table(response.student_data)

  render_last_updated: (timestamp) =>
    time_updated = gettext("Last Updated: <%= timestamp %>")
    full_time_updated = _.template(time_updated, {timestamp: timestamp})
    @$container.find('.last-updated').text full_time_updated

  render_table: (data) =>
    options =
      enableCellNavigation: true
      enableColumnReorder: false
      forceFitColumns: true

    columns = autogenerate_slickgrid_cols(_.first(data), @slickgrid_col_names, @slickgrid_formatters)

    # populate calculated stats for formatters
    @make_calculated_stats(data)

    # create SlickGrid container
    table_placeholder = $ '<div/>', class: 'slickgrid'
    @$container.find('.display-table').append table_placeholder

    # add data to dataview
    update_rows_with_unique_ids(data, (row) -> row.username)
    @dataview.beginUpdate()
    @dataview.setItems(data)
    @dataview.endUpdate()
    
    # initialize grid and add sortable columns as a feature
    @grid = new Slick.Grid(table_placeholder, @dataview, columns, options)

  update_filter: =>
    dataView.setFilterArgs({
      percentCompleteThreshold: percentCompleteThreshold,
      searchString: searchString
    })
    dataView.refresh()

  # fetch distribution data from server.
  # `handler` can be either a callback for success
  # or a mapping e.g. {success: ->, error: ->, complete: ->}
  get_student_analytics_data: (handler) ->
    settings =
      dataType: 'json'
      url: @endpoint

    if typeof handler is 'function'
      _.extend settings, success: handler
    else
      _.extend settings, handler

    $.ajax settings

  make_calculated_stats: (data) =>
    attrs = _.keys(@slickgrid_col_names)
    stats = _.map attrs, (attr) ->
      values = _.pluck(data, attr)
      return {
        avg: get_avg(values)
        stddev: get_stddev(values)
      }

    # Make calculated stats into a map of attr => stats
    # so we can do lookup
    @calculated_stats = _.object(attrs, stats)

class GradeDistributionDisplay
  constructor: ({@$container, @endpoint}) ->
    template_params = {}
    template_html = $('#grade-distributions-widget-template').text()
    @$container.html Mustache.render template_html, template_params
    @$problem_selector = @$container.find '.problem-selector'

  reset_display: ->
    @$container.find('.display-errors').empty()
    @$container.find('.display-text').empty()
    @$container.find('.display-graph').empty()

  show_error: (msg) ->
    @$container.find('.display-errors').text msg

  load: ->
    @get_grade_distributions
      error: std_ajax_err => @show_error gettext("Error fetching grade distributions.")
      success: (data) =>
        time_updated = gettext("Last Updated: <%= timestamp %>")
        full_time_updated = _.template(time_updated, {timestamp: data.time})
        @$container.find('.last-updated').text full_time_updated

        # populate selector
        @$problem_selector.empty()
        for {module_id, block_id, grade_info} in data.data
          label = block_id
          label ?= module_id

          @$problem_selector.append $ '<option/>',
            text: label
            data:
              module_id: module_id
              grade_info: grade_info

        @$problem_selector.change =>
          $opt = @$problem_selector.children('option:selected')
          return unless $opt.length > 0
          @reset_display()
          @render_distribution
            module_id:  $opt.data 'module_id'
            grade_info: $opt.data 'grade_info'

        # one-time first selection of first list item.
        @$problem_selector.change()

  render_distribution: ({module_id, grade_info}) ->
    $display_graph = @$container.find('.display-graph')

    graph_data = grade_info.map ({grade, max_grade, num_students}) -> [grade, num_students]
    total_students = _.reduce ([0].concat grade_info),
      (accum, {grade, max_grade, num_students}) -> accum + num_students

    msg = gettext("<%= num_students %> students scored.")
    full_msg = _.template(msg, {num_students: total_students})
    # show total students
    @$container.find('.display-text').text full_msg

    # render to graph
    graph_placeholder = $ '<div/>', class: 'graph-placeholder'
    $display_graph.append graph_placeholder

    graph_data = graph_data

    $.plot graph_placeholder, [
      data: graph_data
      bars: show: true
      color: '#1d9dd9'
    ]


  # `handler` can be either a callback for success
  # or a mapping e.g. {success: ->, error: ->, complete: ->}
  #
  # the data passed to the success handler takes this form:
  # {
  #   "aname": "ProblemGradeDistribution",
  #   "time": "2013-07-31T20:25:56+00:00",
  #   "course_id": "MITx/6.002x/2013_Spring",
  #   "options": {
  #     "course_id": "MITx/6.002x/2013_Spring",
  #   "_id": "6fudge2b49somedbid1e1",
  #   "data": [
  #     {
  #       "module_id": "i4x://MITx/6.002x/problem/Capacitors_and_Energy_Storage",
  #       "grade_info": [
  #         {
  #           "grade": 0.0,
  #           "max_grade": 100.0,
  #           "num_students": 3
  #         }, ... for each grade number between 0 and max_grade
  #   ],
  # }
  get_grade_distributions: (handler) ->
    settings =
      dataType: 'json'
      url: @endpoint
      data: aname: 'ProblemGradeDistribution'

    if typeof handler is 'function'
      _.extend settings, success: handler
    else
      _.extend settings, handler

    $.ajax settings


# Analytics Section
class InstructorAnalytics
  constructor: (@$section) ->
    @$section.data 'wrapper', @

    @$pd_containers = @$section.find '.profile-distribution-widget-container'
    @$gd_containers = @$section.find '.grade-distributions-widget-container'
    @$sd_container = _.first (@$section.find '.student-analytics-data-widget-container')

    @pdws = _.map (@$pd_containers), (container) =>
      new ProfileDistributionWidget
        $container: $(container)
        feature:    $(container).data 'feature'
        title:      $(container).data 'title'
        endpoint:   $(container).data 'endpoint'

    @gdws = _.map (@$gd_containers), (container) =>
      new GradeDistributionDisplay
        $container: $(container)
        endpoint:   $(container).data 'endpoint'

    @sdw = new StudentAnalyticsDataWidget
      $container: $(@$sd_container)
      endpoint:   $(@$sd_container).data 'endpoint'

  refresh: ->
    for pdw in @pdws
      pdw.load()

    for gdw in @gdws
      gdw.load()

    @sdw.load()

  onClickTitle: ->
    @refresh()


# export for use
# create parent namespaces if they do not already exist.
_.defaults window, InstructorDashboard: {}
_.defaults window.InstructorDashboard, sections: {}
_.defaults window.InstructorDashboard.sections,
  InstructorAnalytics: InstructorAnalytics
