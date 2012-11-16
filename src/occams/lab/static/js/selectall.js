jQuery(function($){
    /*$(document).ready*/
    $(document).ready(function(){
      console.log('document ready')
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
   });

       // No overlays for IE6
       if (!jQuery.browser.msie ||
           parseInt(jQuery.browser.version, 10) >= 7) {
           // Set up overlays
           $("a#specimenfilter").prepOverlay({
               subtype: 'ajax',
               filter: common_content_filter,
               formselector: '#content-core>#form',
               noform: 'reload',
               //redirect: function() {return location.href;},
            });
       }

    var initializeSpecimenAdd = function(){
        $("select[id='form-widgets-specimen_cycle']").empty();
          $("select[id='form-widgets-specimen_cycle']").append(
              $('<option>').attr({
                  id: 'form-widgets-specimen_cycle-novalue',
                  value:'--NOVALUE--',
                  }).text('select a value ...')
              );
              $("#form-widgets-specimen_patient_our").blur(function(event){
                $.ajax({
                    type: 'GET',
                    url:  './@@cycle_by_patient_json',
                    data: {
                    our_number: event.target.value,
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
                });
            });
        };

       // No overlays for IE6
       if (!jQuery.browser.msie ||
           parseInt(jQuery.browser.version, 10) >= 7) {
           // Set up overlays
           $("a#addspecimen").prepOverlay({
               subtype: 'ajax',
               config: {onBeforeLoad: function() {initializeSpecimenAdd();}},
               filter: common_content_filter,
               formselector: '#content-core>form#form',
               noform: 'reload',
               //redirect: function() {return location.href;},
               closeselector: '[name=form.buttons.cancel]'
            });
       }
});