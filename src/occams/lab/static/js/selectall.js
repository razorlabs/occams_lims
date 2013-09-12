(function ($) {
  'use strict';
  $(document).ready(function () {

    // Set up the "Select All" button for all crud forms
    $("input[class='submit-widget button-field']").each(function () {
      if ($(this).attr('name').indexOf("buttons.selectall") <= 0) {
        return;
      }
      $(this).unbind();
      $(this).click(function (event) {
        event.preventDefault();
        if ($(this).attr('value') === 'Select All') {
          $(this).parentsUntil('form').parent().find('td:first-child .single-checkbox-widget').each(function () {
              $(this).attr("checked", true);
          });
          $(this).attr('value', 'Deselect All');
        } else {
          $(this).parentsUntil('form').parent().find('.single-checkbox-widget').each(function () {
              $(this).attr("checked", false);
          });
          $(this).attr('value', 'Select All');
        }
      });
    });

    // Set up cycle listing for adding of specimen
    $(document).delegate('#form-widgets-specimen_patient_our', 'keyup', function(event){
      var $target = $(event.target);
      if( $target.val().length <= 0 ){
        return;
      }
      $.ajax({
        type: 'GET',
        url:  './@@cycle_by_patient_json',
        data: {our_number: $target.val()},
        success: function (response, status, xhr) {
          // use JSON to update the dropdown's option elements
          $("select[id='form-widgets-specimen_cycle']").select2("close");
          $("select[id='form-widgets-specimen_cycle']").empty();
          $("select[id='form-widgets-specimen_cycle']").append(
            $('<option>').attr({
              id: 'form-widgets-specimen_cycle-novalue',
              value: '--NOVALUE--'
            }).text('select a value ...')
          );
          for (var i = 0; i < response.length; i++) {
            $("select[id='form-widgets-specimen_cycle']").append(
              $('<option>').attr({
                id: 'form-widgets-specimen_cycle-' + i,
                value: response[i].name
              }).text(response[i].title + ' (' + response[i].date + ')')
            );
          }
        },
        error: function (response, status, xhr) {
          $("select[id='form-widgets-specimen_cycle']").empty();
          $("select[id='form-widgets-specimen_cycle']").append(
            $('<option>').attr({
              id: 'form-widgets-specimen_cycle-novalue',
              value: '--NOVALUE--'
            }).text('select a value ...')
          );
        }
      });
      $("#s2id_form-widgets-specimen_cycle").select2("val", "");
    });

    // Set up the receipt printer for the aliquot checkout view
    $("input[id='aliquot-checkout-buttons-printreceipt']").wrap('<a id="receiptprinter" href="./receipt" target="_new" />');
    $("#receiptprinter").printPage();

    // prepOverlay only checks src/href/action, ugh... so we have to do this hack where we wrap it in an <a>
    $("input[id='crud-edit-form-buttons-print']").wrap('<a class="js-overlay" href="./printspecimenlabelform" />');
    $("input[id='aliquot-prepared-buttons-print']").wrap('<a class="js-overlay" href="./printaliquotlabelform" />');
    $("input[id='aliquot-checkout-buttons-batchupdate']").wrap('<a class="js-overlay" href="./batchcheckoutform" />');
    $("input[id='crud-edit-form-buttons-addspecimen']").wrap('<a class="js-overlay" href="./addspecimen" />');

    if (!$.browser.msie || parseInt($.browser.version, 10) >= 7) {
      // Set up overlays
      $("#addspecimen, .lab_filter, .js-overlay").prepOverlay({
        subtype: 'ajax',
        filter: common_content_filter,
        formselector: '#content-core>#form',
        noform: 'reload',
        config: {onLoad: function () {
            $("select.occams-select2").select2();
            $(function () {
                $("input.occams-datepicker").datepicker({
                  changeMonth: true,
                  changeYear: true
                });
              });
          },
          onBeforeClose: function () {
            $("select.occams-select2").select2("close");
          }
        },
        closeselector: '[name=form.buttons.cancel],[name=form.buttons.cancel]'
      });
    }

    // I don't know what ths is for
  });

})(jQuery);
