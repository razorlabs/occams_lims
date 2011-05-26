(function($){
    /*$(document).ready*/
    $(window).load(function(){
        $("input[name='crud-edit.form.buttons.selectall']").each(function(){
            $(this).unbind();
            $(this).click(function(event) { 
                event.preventDefault();
                if($(this).attr('value') =='Select All'){
                    $(this).parentsUntil('form').parent().find('.single-checkbox-widget').each(function(){
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
        });
    });
})(jQuery)