$(function () {
  $('[data-toggle="popover"]').popover();
  $('.js-select2').select2({allowClear: true});
  $('.js-date').datetimepicker({useCurrent: false, pickTime: false, format: 'YYYY-MM-DD'});
})

