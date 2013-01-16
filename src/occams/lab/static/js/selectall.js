jQuery(function($){
    /*$(document).ready*/
    $(document).ready(function(){
        $("input[class='submit-widget button-field']").each(function(){
            if ($(this).attr('name').indexOf("buttons.selectall")>0)
            {
                $(this).unbind();
                $(this).click(function(event) {
                    event.preventDefault();
                    if($(this).attr('value') =='Select All'){
                        $(this).parentsUntil('form').parent().find('td:first-child .single-checkbox-widget').each(function(){
                            $(this).attr("checked",true);
                        });
                        $(this).attr('value', 'Deselect All');
                    }else{
                         $(this).parentsUntil('form').parent().find('.single-checkbox-widget').each(function() {
                            $(this).attr("checked",false);
                        });
                        $(this).attr('value', 'Select All');
                    };
                });
            };
        });

        $("#receiptprinter").printPage();
          $("input[id='aliquot-checkout-buttons-printreceipt']").wrap('<a id="receiptprinter" href="./receipt" target="_new" />')

       // No overlays for IE6
       if (!jQuery.browser.msie ||
           parseInt(jQuery.browser.version, 10) >= 7) {
           // Set up overlays
           $("a.lab_filter").prepOverlay({
               subtype: 'ajax',
               filter: common_content_filter,
               formselector: '#content-core>#form',
               noform: 'reload',
               //redirect: function() {return location.href;},
            });
       }
        $("input[id='crud-edit-form-buttons-print']").wrap('<a id="specimenlabelprinter" href="./printspecimenlabelform" />')
       if (!jQuery.browser.msie ||
           parseInt(jQuery.browser.version, 10) >= 7) {
           // Set up overlays
           $("a#specimenlabelprinter").prepOverlay({
               subtype: 'ajax',
               filter: common_content_filter,
               formselector: '#content-core>#form',
               noform: 'reload',
               //redirect: function() {return location.href;},
               closeselector: '[name=form.buttons.close]'
            });
       }
        $("input[id='aliquot-prepared-buttons-print']").wrap('<a id="aliquotlabelprinter" href="./printaliquotlabelform" />')
       if (!jQuery.browser.msie ||
           parseInt(jQuery.browser.version, 10) >= 7) {
           // Set up overlays
           $("a#aliquotlabelprinter").prepOverlay({
               subtype: 'ajax',
               filter: common_content_filter,
               formselector: '#content-core>#form',
               noform: 'reload',
               //redirect: function() {return location.href;},
               closeselector: '[name=form.buttons.close]'
            });
       }
        $("input[id='aliquot-checkout-buttons-batchupdate']").wrap('<a class="batchcheckout" href="./batchcheckoutform" />')
       if (!jQuery.browser.msie ||
           parseInt(jQuery.browser.version, 10) >= 7) {
           // Set up overlays
           $("a.batchcheckout").prepOverlay({
               subtype: 'ajax',
               filter: common_content_filter,
               formselector: '#content-core>#form',
               noform: 'reload',
               //redirect: function() {return location.href;},
               closeselector: '[name=form.buttons.close]'
            });
       }


    var buildCycleList = function(){
      if ($('#form-widgets-specimen_patient_our').length){
      $.ajax({
          type: 'GET',
          url:  './@@cycle_by_patient_json',
          data: {
          our_number: $("#form-widgets-specimen_patient_our").fieldValue()[0],
          },
          success: function(response, status, xhr) {
          // use JSON to update the dropdown's option elements
            $("select[id='form-widgets-specimen_cycle']").empty();
            $("select[id='form-widgets-specimen_cycle']").append(
                $('<option>').attr({
                id: 'form-widgets-specimen_cycle-novalue',
                value:'--NOVALUE--',
                }).text('select a value ...')
            );
            for(var i=0; i < response.length; i++){
                $("select[id='form-widgets-specimen_cycle']").append(
                    $('<option>').attr({
                        id: 'form-widgets-specimen_cycle-' + i,
                        value: response[i]['name'],
                      }).text(response[i]['title'] + ' (' + response[i]['date'] + ')')
                    );
                }
            },
            error: function(response, status, xhr) {
            $("select[id='form-widgets-specimen_cycle']").empty();
            $("select[id='form-widgets-specimen_cycle']").append(
                $('<option>').attr({
                id: 'form-widgets-specimen_cycle-novalue',
                value:'--NOVALUE--',
                }).text('select a value ...')
            );
            },
        });
      }
    };

    var initializeSpecimenAdd = function(){
        buildCycleList();
        $("#form-widgets-specimen_patient_our").blur(function(){
            buildCycleList()
        });
        };

         initializeSpecimenAdd();
        $("input[id='crud-edit-form-buttons-addspecimen']").wrap('<a class="addspecimen" href="./addspecimen" />')
       // No overlays for IE6
       if (!jQuery.browser.msie ||
           parseInt(jQuery.browser.version, 10) >= 7) {
           // Set up overlays
           $("a#addspecimen, a.addspecimen").prepOverlay({
               subtype: 'ajax',
               config: {onLoad: function() {initializeSpecimenAdd();}},
               filter: common_content_filter,
               formselector: '#content-core>form#form',
               noform: 'reload',
               //redirect: function() {return location.href;},
               closeselector: '[name=form.buttons.cancel]'
            });
       }
});
});
