+function($){
  'use strict';

  // general modal window fetch
  // requires data-remote="" attribute and a modal target
  $('button[data-modal-remote]').on('click', function(event){
    var $button = $(event.target),
        $modal = $($button.data('modal-target')),
        remote = $button.data('modal-remote');
      $modal.load(remote, function(response, status, xhr){
        $modal.modal('show');
      });
  });

  // general submit button handler for modal forms
  $(document).on('click', '.modal [type="submit"]', function(event){
    event.preventDefault();
    var $button = $(this),
        $form = $button.closest('form'),
        $modal = $form.closest('.modal'),
        url = $form.attr('action'),
        data = $form.serializeArray();

    // Include the submit button data as well, jQuery doesn't do this...
    data.push({name: $button.attr('name'), value: ''});

    $.post(url, data, function(response, status, xhr){
      var contentType = xhr.getResponseHeader('Content-Type');
      if (contentType.indexOf('pdf') > 0){
        var file = new Blob([response], {type: 'application/pdf'});
        var fileURL = URL.createObjectURL(file);
        window.open(fileURL);
        window.location.reload();
      } else if (contentType.indexOf('json') > 0) {
        window.location = response.__next__
      } else {
        $modal.html(response);
      }
    });
  });

}(jQuery);
