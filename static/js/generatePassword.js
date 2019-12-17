function generatePassword() {
    $.ajax({
        type: 'POST',
        url: 'generatePassword/',
        data: {},
        dataType: 'json',
        success: function (msg) {
            if (msg.password) {
                var generateBtn = $("#generatePasswordBtn");
                generateBtn.parent().append(
                    '<div class="row align-items-center justify-content-center" id="gamePasswordDisplayDiv"></div>'
                );
                var div = $('#gamePasswordDisplayDiv');
                div.append('<p></p>').text('Game Password:  ' + msg.password);
                generateBtn.remove();
            }
        }
    });
}