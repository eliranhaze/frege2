function post_answer(url, data, csrf) {
    empty_msg = is_empty()
    if (empty_msg) {
        $.notify({
            icon: "glyphicon glyphicon-pencil",
            message: "<strong>"+empty_msg+"</strong>"
        },{
            type: "warning",
            delay: 1000,
        });
        register_event();
        return false;
    }
    $("#answer").html("בודק...");
    data['csrfmiddlewaretoken'] = csrf;
    $.post(url, data, function(data, status) {
        on_response(data);
        if (data['correct']) {
            $.notify({
                icon: "glyphicon glyphicon-ok",
                message: "<strong>תשובה נכונה</strong>"
            },{
                type: "success",
            });
            $("#answer").html("המשך");
            $("#answer").attr("onclick", data['next_url']);
            $("#answer").attr("class", "btn btn-primary btn-lg");
            on_success();
        } else {
            if (notify_incorrect(data)) {
                $.notify({
                    icon: "glyphicon glyphicon-remove",
                    message: "<strong>תשובה שגויה</strong>"
                },{
                    type: "danger",
                });
            }
            $("#answer").html("אישור");
            register_event();
        }
    })
    .fail(function(response){
        register_event();
        if (response.responseText) {
            $.notifyClose();
            $.notify({
                message: "<strong>נראה שיש בעיה בשרת...</strong> \
                         <br>הבעיה נרשמה והיא תטופל בהקדם. \
                         <br>תודה על הסבלנות. \
                         <br>בינתיים, הנה לב ממני: <span class='glyphicon glyphicon-heart'></span>"
            },{
                type: "info",
                allow_dismiss: true,
                newest_on_top: true,
                delay: 15000,
            });
            $("#answer").html("אישור");
        } else {
            $.notify({
                icon: "glyphicon glyphicon-flash",
                message: "<strong>בעיה בהתחברות לשרת</strong> אנא בדקו את החיבור לאינטרנט"
            },{
                type: "warning",
            });
            $("#answer").html("אישור");
        }
    });
}

$(document).ready(function() {
    $.notifyDefaults({
        allow_dismiss: false,
        offset: 100,
        placement: {from: "bottom", align: "center"},
        animate: {enter: "animated fadeIn", exit: "animated fadeOut"},
        delay: 2000,
    });
});
