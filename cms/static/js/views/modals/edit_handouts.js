define(["js/views/modals/base_modal", "js/views/course_info_helper"],
    function(BaseModal, CourseInfoHelper) {
        var EditHandoutsModal = BaseModal.extend({
            events: {
                "click .action-save": "save",
            },

            options: $.extend({}, BaseModal.prototype.options, {
                addSaveButton: true
            }),

            initialize: function() {
                BaseModal.prototype.initialize.call(this);
                this.events = _.extend({}, BaseModal.prototype.events, this.events);
                this.template = this.loadTemplate('edit-course-handouts');
            },

            edit: function(content, base_asset_url) {
                this.show();
                this.$('.handouts-content-editor').html(content);
                CourseInfoHelper.editWithTinyMCE(
                    base_asset_url, this.$('.handouts-content-editor').get(0).id); 
                this.$('.modal-window-title').text('STUPID');
                this.resize();
            },

            getContentHtml: function() {
                return this.template();
            },

            save: function() {
                //move code from course_info_handouts.js
            }
        });

        return EditHandoutsModal;
    });
