(function ($) {
  'use strict';
  $(document).ready(
    // Set up the "Select All" button for all crud forms
    function () {
      $("input[class='submit-widget button-field']").each(
        function () {
          if ($(this).attr('name').indexOf("buttons.selectall") > 0) {
            $(this).unbind();
            $(this).click(
              function (event) {
                event.preventDefault();
                if ($(this).attr('value') === 'Select All') {
                  $(this).parentsUntil('form').parent().find('td:first-child .single-checkbox-widget').each(
                    function () {
                      $(this).attr("checked", true);
                    }
                  );
                  $(this).attr('value', 'Deselect All');
                } else {
                  $(this).parentsUntil('form').parent().find('.single-checkbox-widget').each(
                    function () {
                      $(this).attr("checked", false);
                    }
                  );
                  $(this).attr('value', 'Select All');
                }
              }
            );
          }
        }
      );
      // Set up the receipt printer for the aliquot checkout view
      $("input[id='aliquot-checkout-buttons-printreceipt']").wrap('<a id="receiptprinter" href="./receipt" target="_new" />');
      $("#receiptprinter").printPage();

      // Set up overlay for the lab filter
      // No overlays for IE6
      if (!$.browser.msie ||
          parseInt($.browser.version, 10) >= 7) {
        // Set up overlays
        $("a.lab_filter").prepOverlay({
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
          }
        });
      }
      // Set up overlay for specimen label printer
      $("input[id='crud-edit-form-buttons-print']").wrap('<a id="specimenlabelprinter" href="./printspecimenlabelform" />');

      if (!$.browser.msie ||
          parseInt($.browser.version, 10) >= 7) {
        // Set up overlays
        $("a#specimenlabelprinter").prepOverlay({
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
          closeselector: '[name=form.buttons.close]'
        });
      }
      // Set up overlay for aliquot label printer
      $("input[id='aliquot-prepared-buttons-print']").wrap('<a id="aliquotlabelprinter" href="./printaliquotlabelform" />');
      if (!$.browser.msie ||
          parseInt($.browser.version, 10) >= 7) {
        // Set up overlays
        $("a#aliquotlabelprinter").prepOverlay({
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
          closeselector: '[name=form.buttons.close]'
        });
      }
  //     // Set up overlay for batch updating aliquot pending checkout
      $("input[id='aliquot-checkout-buttons-batchupdate']").wrap('<a class="batchcheckout" href="./batchcheckoutform" />');
      if (!$.browser.msie ||
          parseInt($.browser.version, 10) >= 7) {
        // Set up overlays
        $("a.batchcheckout").prepOverlay({
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
          closeselector: '[name=form.buttons.close]'
        });
      }
  //     // Set up the add specimen overlay
      $("input[id='crud-edit-form-buttons-addspecimen']").wrap('<a class="addspecimen" href="./addspecimen" />');
      // Set up cycle listing for adding of specimen
      var buildCycleList = function () {
        var i = 0;
        if ($('#form-widgets-specimen_patient_our').length) {
          $.ajax({
            type: 'GET',
            url:  './@@cycle_by_patient_json',
            data: {
              our_number: $("#form-widgets-specimen_patient_our").fieldValue()[0]
            },
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
              for (i; i < response.length; i++) {
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
        }
      };
      // Initialize the specimen add form to use the buildCycleList function
      var initializeSpecimenAdd = function () {
        buildCycleList();
        $("#form-widgets-specimen_patient_our").blur(
          function () {
            buildCycleList();
            $("#s2id_form-widgets-specimen_cycle").select2("val", "");
          }
        );
      };
      initializeSpecimenAdd();
      // No overlays for IE6
      if (!$.browser.msie ||
          parseInt($.browser.version, 10) >= 7) {
        // Set up overlays
        $("a#addspecimen, a.addspecimen").prepOverlay({
          subtype: 'ajax',
          config: {onLoad: function () {
              initializeSpecimenAdd();
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
          filter: common_content_filter,
          formselector: '#content-core>form#form',
          noform: 'reload',

          closeselector: '[name=form.buttons.cancel]'
        });
      }
    }
  );
})(jQuery);