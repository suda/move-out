// Generated by CoffeeScript 1.8.0
(function() {
  $(document).ready(function() {
    return $(document).on('submit', 'form', function(e) {
      var parent, url;
      url = $(this).attr('action');
      parent = $(this).closest('.thing-name');
      e.preventDefault();
      return $.ajax(url, {
        type: 'POST',
        dataType: 'json',
        data: $(this).serialize() + "&is_ajax=1",
        success: function(data, status, jqXHR) {
          parent.find('form').remove();
          return parent.append(data.form);
        }
      });
    });
  });

}).call(this);
