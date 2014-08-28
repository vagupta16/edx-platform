define(["js/views/baseview", "js/views/course_info_helper", "js/views/modals/edit_handouts"],
    function(BaseView, CourseInfoHelper, EditHandoutsModal) {

    // the handouts view is dumb right now; it needs tied to a model and all that jazz
    var CourseInfoHandoutsView = BaseView.extend({
        // collection is CourseUpdateCollection
        events: {
            "click .edit-button" : "onEdit"
        },

        initialize: function() {
            this.template = this.loadTemplate('course_info_handouts');
            var self = this;
            this.model.fetch({
                complete: function() {
                    self.render();
                },
                reset: true
            });
        },

        render: function () {
            CourseInfoHelper.changeContentToPreview(
                this.model, 'data', this.options['base_asset_url']);

            this.$el.html(
                $(this.template({
                    model: this.model
                }))
            );
            $('.handouts-content').html(this.model.get('data'));
            this.$preview = this.$el.find('.handouts-content');

            return this;
        },

        onEdit: function(event) {
            var self = this;

            var modal = new EditHandoutsModal();
            return modal.edit(self.model, self.options['base_asset_url'], _.bind(this.render, this));
        }
    });

    return CourseInfoHandoutsView;
}); // end define()
