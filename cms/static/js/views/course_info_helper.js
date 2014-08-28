define(["tinymce", 'js/utils/handle_iframe_binding', "utility"],
    function(TinyMCE, IframeBinding) {
        var editWithTinyMCE = function(baseAssetUrl, textAreaId) {
            this.setupTinyMCE = function(ed) {
              ed.on('SaveImage', function(data) {
                if (data['src']) {
                  return data['src'] = rewriteStaticLinks(data['src'], '/static/', baseAssetUrl);
                }
              });
              ed.on('EditImage', function(data) {
                if (data['src']) {
                  return data['src'] = rewriteStaticLinks(data['src'], baseAssetUrl, '/static/');
                }
              });
              ed.on('SaveLink', function(data) {
                if (data['href']) {
                  return data['href'] = rewriteStaticLinks(data['href'], '/static/', baseAssetUrl);
                }
              });
              ed.on('EditLink', function(data) {
                if (data['href']) {
                  return data['href'] = rewriteStaticLinks(data['href'], baseAssetUrl, '/static/');
                }
              });
              ed.on('ShowCodeEditor', function(source) {
                var content;
                content = rewriteStaticLinks(source.content, baseAssetUrl, '/static/');
                return source.content = content;
              });
              ed.on('SaveCodeEditor', function(source) {
                var content;
                content = rewriteStaticLinks(source.content, '/static/', baseAssetUrl);
                return source.content = content;
              });
            };

            var tiny_mce_css_links = [];
            $("link[rel=stylesheet][href*='tinymce']").filter("[href*='content']").each(function() {
              tiny_mce_css_links.push($(this).attr("href"));
            });
            tinyMCE.baseURL = baseUrl + "js/vendor/tinymce/js/tinymce";
            tinyMCE.init({
                selector: '#' + textAreaId,
                theme: 'modern',
                skin: 'studio-tmce4',
                schema: 'html5',
                convert_urls: false,
                content_css: tiny_mce_css_links.join(", "),
                formats: {
                  code: {
                    inline: 'code'
                  }
                },
                visual: false,
                plugins: "textcolor, link, image, codemirror",
                codemirror: {
                  path: baseUrl + "js/vendor/"
                },
                image_advtab: true,
                toolbar: "formatselect | fontselect | bold italic underline forecolor | bullist numlist outdent indent blockquote | link unlink image | code",
                block_formats: "Paragraph=p;Preformatted=pre;Heading 1=h1;Heading 2=h2;Heading 3=h3",
                height: '400px',
                menubar: false,
                statusbar: false,
                valid_children: "+body[style]",
                valid_elements: "*[*]",
                extended_valid_elements: "*[*]",
                invalid_elements: "",
                setup: this.setupTinyMCE,
                init_instance_callback: function(ed) {
                  return ed.focus();
                }
            });
        };

        var changeContentToPreview = function (model, contentName, baseAssetUrl) {
            var content = rewriteStaticLinks(model.get(contentName), '/static/', baseAssetUrl);
            // Modify iframe (add wmode=transparent in url querystring) and embed (add wmode=transparent as attribute)
            // tags in html string (content) so both tags will attach to dom and don't create z-index problem for other popups
            // Note: content is modified before assigning to model because embed tags should be modified before rendering
            // as they are static objects as compared to iframes
            content = IframeBinding.iframeBindingHtml(content);
            model.set(contentName, content);
            return content;
        };

        return {'editWithTinyMCE': editWithTinyMCE, 'changeContentToPreview': changeContentToPreview};
    }
);
