/*
 * functions for handling question-related server requests
 */

// general post function
function post(url, csrf, postData, onSuccess) {
    if (!postData) {
        postData = {};
    }
    postData['csrfmiddlewaretoken'] = csrf
    $.post(url, postData, function(data, status) {
        if (data['msg']) {
            errmsg(data['msg']);
        } else {
            onSuccess();
        }
    })
    .fail(function(response) {
        errhandler(response);
    });
}

function sbt(url, csrf) {
    $.post(url, {'csrfmiddlewaretoken':csrf}, function(data, status) {
        if (data['next']) window.location.assign(data['next']);
        else errmsg('עברת את מספר הנסיונות המירבי לפרק זה');
    })
    .fail(function(response) {
        errhandler(response);
    });
}

function ans(url, csrf) {
    var emptyMsg = isEmpty();
    if (emptyMsg) {
        errmsg(emptyMsg);
        reg();
        return false;
    }
    var btn = $("#answer");
    btn.html("שולח...");
    var data = getPostData();
    var ajaxkw = {
        url: url,
        type: 'POST',
        data: data,
        success: ansDone(btn),
    };
    if (data instanceof FormData) {
        ajaxkw.processData = false;
        ajaxkw.contentType = false;
        ajaxkw.xhr = function() {
            var xhr = new window.XMLHttpRequest();
            $('#upload-pct').text('0%');
            xhr.upload.addEventListener("progress", function(evt) {
              if (evt.lengthComputable) {
                  var pct = evt.loaded / evt.total;
                  pct = parseInt(pct * 100);
                  if (pct == 100) pct = 99;
                  $('#upload-pct').text(pct+'%');
              }
            }, false);
            return xhr;
        };
    } else {
        data['csrfmiddlewaretoken'] = csrf;
    }
    $.ajax(ajaxkw).fail(function(response){
        errhandler(response);
        btn.html("אישור");
        reg();
    });
}

function ansDone(btn) {
    return function(data, status) {
        btn.html("אישור");
        handleResponse(data);
        if (!data['next']) {
            if (data['msg']) {
                errmsg(data['msg']);
            }
            return;
        }
        if (data['ans_time']) {
            $('#ans-time').text('ענית על שאלה זו ב-'+data['ans_time']);
        }
        okmsg('תשובה נשמרה');
        ansOk(); // callback for specific question types
        reg();
        btn.html("אישור");
        if (data['complete']) {
            $("#sum").css('display', 'inline');
            if (!data['has_followup']) {
                $("#next").hide();
            }
        } else {
            $("#next").attr("onclick", data['next']);
            $("#next").show();
            $("#sum").css('display', 'none');
        }
    }
}

function errhandler(response) {
    if (response.responseText) {
        $.notifyClose();
        $.notify({
            message: "<strong>נראה שיש בעיה בשרת...</strong> \
                     <br>אנא דווחו על כך בהקדם. \
                     <br>תודה. <span class='glyphicon glyphicon-heart'></span>"
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
}

function okmsg(msg) {
    $.notify({
        message: msg
    },{
        template:
          '<div data-notify="container" class="col-xs-11 col-sm-3 alert text-center note ok" role="alert">' +
            '<span data-notify="dismiss">' +
              '<span data-notify="message">{2}</span>' +
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
        delay: 2000,
    });
});


// function for inserting text at cursor position
$.fn.extend({
    insertAtCaret: function(myValue){
        return this.each(function(i) {
            if (document.selection) {
                //For browsers like Internet Explorer
                this.focus();
                var sel = document.selection.createRange();
                sel.text = myValue;
                this.focus();
            } else if (this.selectionStart || this.selectionStart == '0') {
                //For browsers like Firefox and Webkit based
                var startPos = this.selectionStart;
                var endPos = this.selectionEnd;
                var scrollTop = this.scrollTop;
                this.value = this.value.substring(0, startPos)+myValue+this.value.substring(endPos,this.value.length);
                this.focus();
                this.selectionStart = startPos + myValue.length;
                this.selectionEnd = startPos + myValue.length;
                this.scrollTop = scrollTop;
            } else {
                this.value += myValue;
                this.focus();
            }
        });
    }
});
function insert(text) {
    $("#ftxt").insertAtCaret(text);
    $("#ftxt").focus();
}

// bind symbol buttons to insertions
$(document).ready(function() {
    $("#extbtns").find("input").click(function() {
        insert(this.value);
    });
});
