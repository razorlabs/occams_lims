(function($){
    /*$(document).ready*/
    $(window).load(function(){
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
})(jQuery)