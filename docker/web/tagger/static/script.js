/*
TODO Popup will go to the first instance of a name, not necessarily the hover
TODO Caching
TODO Popup loading bar
TODO Pretify box
TODO Graph bars for tags
*/

var users = [];

function hideTooltip() {
    clearTimeout(tooltipTimeout);
    $(".tooltip").fadeOut().remove();
}

function sort(dict){
    var items = Object.keys(dict).map(function(key) {
        return [key, dict[key]];
    });

    items.sort(function(first, second) {
        return second[1] - first[1];
    });

    return items;
}


function popup(data, elementId) {
    var outstr = "";

    items = sort(data);
    items.forEach(function(element){
        outstr += "<span class='tag'>" + element[0] + "</span> " + element[1] + "<br />";
    });
//    for(key in data) {
//        outstr += "<span class='tag'>" + key + "</span> " + data[key] + "<br />";
//    }

    var tooltip = $("<div id='tooltip' class='tooltip'>" + outstr+ "</div>");
    tooltip.appendTo($("#" + elementId));
}

 function showMessage(message, elementId){
    var tooltip = $("<div id='tooltip' class='tooltip'>" + message + "</div>");
    tooltip.appendTo($("#" + elementId));
}

function showTooltip(elementId){
    var user = elementId.substr(7);
    console.log("Loading tooltip for " + user);


    $.ajax({
      cached: true,
      dataType: "json",
      url: "/user/?id=" + user,
      statusCode:{
        200: function(data) {
            popup(data, elementId);
        },
        204: function() {
            showMessage('No tags for user', elementId);
        },
        404: function(data) {
            showMessage(data['message'], elementId);
        }
      }
    });


}

$(".hnuser").hover(function(e) {
    tooltipTimeout = setTimeout(function() { showTooltip(e.target.id) }, 1000);},
    hideTooltip);

$body = $("body");

//$(document).on({
//    ajaxStart: function() { $body.addClass("loading");    },
//     ajaxStop: function() { $body.removeClass("loading"); }
//});

