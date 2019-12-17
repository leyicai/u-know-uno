// To start channel: docker run -p 6379:6379 -d redis:2.8

// room chat
var gameID = window.location.pathname.toString().split('/')[2];
var wsScheme = window.location.protocol == "https:" ? "wss://" : "ws://";
var chatSocket = new WebSocket(wsScheme + window.location.host + '/game/ws/chat/' + gameID + '/');

//receive message
chatSocket.onmessage = function (e) {
    var data = JSON.parse(e.data);
    if (data.hasOwnProperty('type') && data['type'].toString() === 'reload_message') {
        location.reload();
    } else {
        // console.log(data['friends']);
        var message = data['message'].toString();
        // console.log(message === "");
        // console.log(message);
        // if(!message){
        if (message === "") {
        } else {
            var myname = document.querySelector("#username").value;
            var othername = data['username'].toString();
            // $(document.createElement('div')).appendTo("#message").addClass("form-inline row");
            if (myname === othername) {
                $(document.createElement('div')).text(message).appendTo("#message").addClass("sended-message");
            } else {
                $(document.createElement('div')).text(othername + ":").appendTo("#message").addClass("name");
                $(document.createElement('div')).text(message).appendTo("#message").addClass("received-message");
            }
            $("#message").stop().animate({ scrollTop: $("#message")[0].scrollHeight});
        }
    }
};

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly');
};

// document.querySelector('#chat-message-input').focus();
document.querySelector('#chat-message-input').onkeyup = function (e) {
    if (e.keyCode === 13) { // enter, return
        document.querySelector('#chat-message-submit').click();
    }
};

document.querySelector('#chat-message-submit').onclick = function (e) {
    e.preventDefault();
    var messageInputDom = document.querySelector('#chat-message-input');
    var message = messageInputDom.value;
    var username = document.querySelector('#username').value;
    chatSocket.send(JSON.stringify({
        'message': message,
        'username': username,
        'friends': ""
    }));
    document.querySelector('#chat-message-input').value = "";
    // messageInputDom.value = '';
};
