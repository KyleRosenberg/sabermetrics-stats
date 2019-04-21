"use strict";

$(document).ready(function() {
   console.log('Hello Sabermetrites!');
   $('.ui.dropdown').dropdown();
});

function showError(message){
    error = $.parseHTML(`<div class="ui transition hidden error message">
        <div class="header">
            Something went wrong...
        </div>
        ${message}
    </div>`);
    $('body').append(error)
    $(error).transition({
        animation: 'vertical flip in'
    }).transition({
        animation: 'vertical flip out',
        interval: 5000,
        onComplete: function(){
            $(error).remove();
        }
    })
}
