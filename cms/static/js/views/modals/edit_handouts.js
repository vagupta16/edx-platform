define(["js/views/modals/base_modal", "js/views/course_info_helper", "js/views/feedback_notification"],
    function(BaseModal, CourseInfoHelper, NotificationView) {
        var htmlHeight = $('html').height();
        
        var EditHandoutsModal = BaseModal.extend({
            events: {
                "click .action-save": "save",
            },

            options: $.extend({}, BaseModal.prototype.options, {
                addSaveButton: true,
                viewSpecificClasses: 'modal-editor'
            }),

            initialize: function() {
                BaseModal.prototype.initialize.call(this);
                this.events = _.extend({}, BaseModal.prototype.events, this.events);
                this.template = this.loadTemplate('edit-course-handouts');
            },

            edit: function(model, base_asset_url, refresh) {
                $('html').css({'height': '100%', 'overflow': 'hidden'});
                this.model = model;
                this.refresh = refresh;
                this.show();

                this.$('.handouts-content-editor').html(this.model.get('data'));
                CourseInfoHelper.editWithTinyMCE(
                    base_asset_url, this.$('.handouts-content-editor').get(0).id);
                this.resize();
            },

            getContentHtml: function() {
                return this.template();
            },

            save: function() {
                $('html').css({'height': htmlHeight, 'overflow': 'auto'});
                this.model.set('data', tinymce.activeEditor.getContent({format: 'raw', no_events: 1}));
                var saving = new NotificationView.Mini({
                    title: gettext('Saving&hellip;')
                });
                saving.show();
                this.model.save({}, {
                    success: function() {
                        saving.hide();
                    }
                });
                this.hide();
                this.refresh();

                analytics.track('Saved Course Handouts', {
                    'course': course_location_analytics
                });
            },
            
            cancel: function() {
                BaseModal.prototype.cancel.call(this);
                $('html').css({'height': htmlHeight, 'overflow': 'auto'});
            }
        });

        return EditHandoutsModal;
    });
