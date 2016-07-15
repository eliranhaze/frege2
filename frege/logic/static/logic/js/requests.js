/*
 * functions for handling question-related server requests
 */

function postAns(url, data, csrf) {
    var emptyMsg = is_empty()
    if (emptyMsg) {
        errmsg(emptyMsg);
        reg();
        return false;
    }
    $("#answer").html("שולח...");
    data['csrfmiddlewaretoken'] = csrf;
    $.post(url, data, function(data, status) {
        on_response(data);
        okmsg('תשובה נשמרה');
        reg();
        $("#answer").html("אישור");
        if (data['complete']) {
            $("#next").remove();
            $("#sum").css('visibility', 'visible');
        }
        else {
            $("#next").attr("onclick", data['next']);
            $("#next").css('visibility', 'visible');
        }
    })
    .fail(function(response){
        reg();
        $("#answer").html("אישור");
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
        } else {
            $.notify({
                icon: "glyphicon glyphicon-flash",
                message: "<strong>בעיה בהתחברות לשרת</strong> אנא בדקו את החיבור לאינטרנט"
            },{
                type: "warning",
            });
        }
    });
}

function okmsg(msg) {
    $.notify({
        message: msg
    },{
        template:
          '<div data-notify="container" class="col-xs-11 col-sm-3 alert text-center note ok" role="alert">' +
            '<span data-notify="dismiss">' +
              '<span data-notify="message">{2} ☑</span>' +
            '</span>' +
          '</div>'
    });
}

function errmsg(msg) {
    $.notify({
        message: msg
    },{
        template:
          '<div data-notify="container" class="col-xs-11 col-sm-3 alert text-center note" role="alert">' +
            '<span data-notify="dismiss">' +
              '<span data-notify="message">{2}</span>' +
            '</span>' +
          '</div>'
    });
}

$(document).ready(function() {
    $.notifyDefaults({
        allow_dismiss: true,
        offset: {x: 0, y: 200},
        placement: {from: "bottom", align: "center"},
        animate: {enter: "animated fadeIn", exit: "animated fadeOut"},
        delay: 1500,
    });
});
