$(function () {
  $('[data-toggle="popover"]').popover();
  $('.js-select2').select2({allowClear: true});
  $('.js-date').datetimepicker({useCurrent: false, pickTime: false, format: 'YYYY-MM-DD'});

  //this handling of modals is preferred as bootstrap remote modal handling
  //is deprecated and will be removed in bootstrap 4
  //if we move LIMS to knockout, we could use the click binding here instead
  $('#add-modal').on('click', function(event) {
      event.preventDefault();
      var $this = $(this);
      var remote = $this.data('remote');
      $('#modal-target').load(remote);
      var modal = $('#modal-target').modal()
      modal.show()
  });
})

