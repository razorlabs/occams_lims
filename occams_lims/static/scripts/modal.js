+function($){
  'use strict';

  // general modal window fetch
  // requires data-remote="" attribute and a modal target
  $('button[data-modal-remote]').on('click', function(event){
    var $button = $(event.target),
        // Grab id of object triggering modal; tal:repeat index row for example
        // see checked-in.pt for repeat .index example (line 95)
        data = this.id,
        $modal = $($button.data('modal-target')),
        remote = $button.data('modal-remote');
        // Sets data-target variable to id of the object calling the modal
        $modal.attr('data-target', data);
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

        // Use FileSaver polyfill to prompt for download instead of popup
        var file = new Blob([response], {type: 'application/pdf'});
        saveAs(file)

        // Ensure the page refreshes after save
        setTimeout(function() { window.location.reload(); }, 100);

      } else if (contentType.indexOf('json') > 0) {
        window.location = response.__next__
      } else {
        $modal.html(response);
      }
    });
  });

}(jQuery);
