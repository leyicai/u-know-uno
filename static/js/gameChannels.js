// game

var gameID = window.location.pathname.toString().split('/')[2];
var wsScheme = window.location.protocol == "https:" ? "wss://" : "ws://";
var gameSocket = new WebSocket(wsScheme + window.location.host + '/game/ws/' + gameID + '/');
var timer;
var started = false;
var globalCurrentColor = "wild";
var globalCurrentOrder = "counterclockwise";
var waitUNO = false;
/***************** consumer to websocket **********************/

gameSocket.onmessage = function (e) {
    var data = JSON.parse(e.data);
    // console.log(data);
    var type = data['type'];
    if (type == "update_game") {
        updateGame(data['game']);
    } else if (type == "init_cards") {
        initCards(data['init_cards']);
    } else if (type == "draw_card") {
        drawCard(data);
    } else if (type == "update_draw_card") {
        updateDrawCard(data);
    } else if (type == "play_card") {
        playCard(data);
    } else if (type == "update_play_card") {
        updatePlayCard(data);
    } else if (type == "update_uno") {
        updateUno(data);
    } else if (type == "end_game") {
        alert("Game is Over! You'll be redirect to the result page");
        started = false;
        window.location.href = 'end/';
    }
    updateCurrentUser(data['current_player']);
    if (started == true) {
        updateCurrentRound(data['current_player_order']);
    }
};

/** helper function to update current user **/
function updateCurrentUser(curUsername) {
    var username = $('#username').val();
    var progressDiv = $('#progress');
    var progressBarDiv = $('#progressBar');
    var yourRound = $('#yourRound');

    if (curUsername == username) {
        if (yourRound.css("display") == "none") {
            waitUNO = false;
            // console.log("remove waiting uno..");

            yourRound.css("display", "block");
            // yourRound.addClass(" animated shake");

            progressBarDiv.css("border", "1px #669CB8 solid");
            progressBarDiv.css("-webkit-box-shadow", " 0 2px 2px #D0D4D6");
            progressBarDiv.css("background", "-webkit-gradient(linear, 0 0, 0 100%, from(#E1E9EE), to(white))");
            progressDiv.css("-webkit-transition", "width 60s ease-in-out");
            progressDiv.css("width", "100%");
            timer = window.setTimeout(function () {

                $('#yourRound').css("display", "none");

                progressDiv.css("-webkit-transition", "width 0s ease-in-out");
                progressDiv.css("width", "0%");
                progressBarDiv.css("border", "0px #669CB8 solid");
                progressBarDiv.css("-webkit-box-shadow", " 0 0 0 #D0D4D6");
                progressBarDiv.css("background", "inherit");

                gameSocket.send(JSON.stringify({
                    'action': 'timeout',
                }));
            }, 60000);
            // console.log("set timer:" + timer);
        }
    } else {
        // console.log("clearing timer:" + timer);
        clearTimeout(timer);
        progressDiv.css("-webkit-transition", "width 0s ease-in-out");
        progressDiv.css("width", "0%");
        progressBarDiv.css("border", "0px #669CB8 solid");
        progressBarDiv.css("-webkit-box-shadow", " 0 0 0 #D0D4D6");
        progressBarDiv.css("background", "inherit");
        $('#yourRound').css("display", "none");


    }
}

/** helper function to update current round place **/
function updateCurrentRound(curPlayerOrder) {
    // console.log("curPlayerOrder:" + curPlayerOrder);
    var curOrder = parseInt($('#curOrder').val());
    var rightCur = $('#rightPlayerCurrent');
    var topCur = $('#topPlayerCurrent');
    var leftCur = $('#leftPlayerCurrent');
    var relativeOrder = parseInt(curPlayerOrder) - curOrder;
    if (relativeOrder < 0) {
        relativeOrder += 4;
    }
    // console.log("relativePlayerOrder:" + relativeOrder);
    if (relativeOrder == 1) {
        rightCur.css("display", "block");
        topCur.css("display", "none");
        leftCur.css("display", "none");
    } else if (relativeOrder == 2) {
        rightCur.css("display", "none");
        topCur.css("display", "block");
        leftCur.css("display", "none");
    } else if (relativeOrder == 3) {
        rightCur.css("display", "none");
        topCur.css("display", "none");
        leftCur.css("display", "block");
    } else {
        rightCur.css("display", "none");
        topCur.css("display", "none");
        leftCur.css("display", "none");
    }
}

/** before game start, when someone get in the room or get ready, update game. **/
function updateGame(game) {
    var username = $('#username').val();
    var players = game.players;
    // find current player order and ready status
    for (var i = 0; i < players.length; i++) {
            if (players[i].username == username) {
                $('#curOrder').val(players[i].order);
                if (players[i].is_ready == false) {
                    $('#readyBtn').css("display", "block");
                }
                break;
            }
        }
        //show other players
        var curOrder = parseInt($('#curOrder').val());
        var relativeOrder;
        $('#playerInRoom').html("");
        //remove all players
        removeAllPlayer();
        //load current player one by one
        for (var j = 0; j < players.length; j++) {
            showPlayerInfo(players[j]);
            if (players[j].username == username) continue;
            relativeOrder = (parseInt(players[j].order) - curOrder) % 4;
            if (relativeOrder < 0) {
                relativeOrder += 4;
            }
            if (relativeOrder == 1) {
                loadOtherPlayer(players[j], "right");
            } else if (relativeOrder == 2) {
                loadOtherPlayer(players[j], "top");
            } else {
                loadOtherPlayer(players[j], "left");
            }
        }
    //if game started, remove ready label, show deck and current card
    if (game.is_started == true) {
        started = true;
        initializeCurrentCard(game.current_card);
        $('#passwordDiv').css("display", "none");
        $('#deckDiv').css("display", "block");
        $('#currentCardDiv').css("display", "block");

        var currentColor = $('#currentColor');

        document.getElementById("currentColor").removeAttribute("class");

        if (game.current_card.color == "wild") {
            // console.log("current card is wild card, color :", game.current_card.temp_color);
            currentColor.addClass(game.current_card.temp_color);
            globalCurrentColor = game.current_card.temp_color;

        } else {
            // console.log("current card is not wild card, color :", game.current_card.color);
            currentColor.addClass(game.current_card.color);
            globalCurrentColor = game.current_card.color;
        }
        currentColor.css("display", "block");
        $('#currentColorLabel').css("display", "block");

        //set is reversed?
        if (game.is_reverse == true) {
            $('#clockwise').css("display", "inline");
            globalCurrentOrder = "clockwise";
        } else {
            $('#counterclockwise').css("display", "inline");
            globalCurrentOrder = "counterclockwise";
        }
        $('#currentOrder').css("display", "block");

        $('#currentOrderLabel').css("display", "inline");

        $('#currentCardDiv').css("display", "block");
        $('#ready').css("display", "none");
        $('#buttonRow').css("display", "none");
        $('#rightPlayerReady').css("display", "none");
        $('#topPlayerReady').css("display", "none");
        $('#leftPlayerReady').css("display", "none");
        $('#unoButton').css("display", "block");
    }
}

/** helper function to remove all player in room before reload game status **/
function removeAllPlayer() {
    //hide all player name
    $('#rightPlayerName').css("display", "none");
    $('#leftPlayerName').css("display", "none");
    $('#topPlayerName').css("display", "none");

    //hide all player card
    $('#rightPlayerCards').css("display", "none");
    $('#leftPlayerCards').css("display", "none");
    $('#topPlayerCards').css("display", "none");

    //remove all ready
    $('#rightPlayerReady').css("display", "none");
    $('#leftPlayerReady').css("display", "none");
    $('#topPlayerReady').css("display", "none");

    //remove all uno
    $('#rightPlayerUno').css("display", "none");
    $('#leftPlayerUno').css("display", "none");
    $('#topPlayerUno').css("display", "none");
}

/** helper function to load newly come-in user's info **/
function loadOtherPlayer(player, position) {
    var nameDiv = $('#' + position + 'PlayerName');
    nameDiv.html(player.username);
    //show player name
    nameDiv.css("display", "block");
    //show player card
    $('#' + position + 'PlayerCards').css("display", "block");
    // if is_ready show ready
    if (player.is_ready == true) {
        $('#' + position + 'PlayerReady').css("display", "block");
    }
    // if uno show uno
    if (player.uno == true) {
        $('#' + position + 'PlayerUno').css("display", "block");
    }
}

/** get initial cards when game starts **/
function initCards(cards) {
    for (var i = 0; i < cards.length; i++) {
        getOneCard(cards[i], " animated flipInX fast");
    }
}

/** other player play a card, display the effect and show whether he calls uno **/
function updatePlayCard(data) {
    var curOrder = parseInt($('#curOrder').val());
    var relativeOrder = parseInt(data['player']) - curOrder;
    var currentColor = $('#currentColor');
    if (relativeOrder < 0) {
        relativeOrder += 4;
    }
    var card = data['card'];
    // play card effect
    if (relativeOrder == 1) {
        playCardEffect(card.id, card.color, card.card_type, card.img_src, "bounceInRight");
        if (data['uno'] == true)
            $('#rightPlayerUno').css("display", "block");
    } else if (relativeOrder == 2) {
        playCardEffect(card.id, card.color, card.card_type, card.img_src, "bounceInDown");
        if (data['uno'] == true)
            $('#topPlayerUno').css("display", "block");
    } else if (relativeOrder == 3) {
        playCardEffect(card.id, card.color, card.card_type, card.img_src, "bounceInLeft");
        if (data['uno'] == true)
            $('#leftPlayerUno').css("display", "block");
    }
    //action card and wild card effect
    actionAndWildCardEffect(card.card_type);
    //update currentColor
    document.getElementById("currentColor").removeAttribute("class");
    currentColor.addClass(card.color);
    globalCurrentColor = card.color;
}

/** action card and wild card effect **/
function actionAndWildCardEffect(card_type) {
    //skip effect
    if (card_type == "skip") {
        skipEffect();
    }
    //reverse effect
    if (card_type == "reverse") {
        reverseEffect();
    }
    //wildChangeEffect
    if (card_type == "change") {
        wildChangeEffect();
    }
    //+2 or +4
    if (card_type == "draw2" || card_type == "draw4") {
        draw2OrDraw4Effect();
    }
}

/** skip card effect **/
function skipEffect() {
    // console.log("skipEffect!");
    var skip = $('#skip');
    var skipImg = $('#skipImg');
    skip.css("display", "block");
    skipImg.addClass(" animated heartBeat fast");
    setTimeout(function () {
        skip.css("display", "none");
    }, 1000);
}

/** reverse card effect **/
function reverseEffect() {
    var clockwise = $('#clockwise');
    var counterclockwise = $('#counterclockwise');

    //reverse animation
    var reverse = $('#reverse');
    var reverseImg = $('#reverseImg');
    reverse.css("display", "block");
    reverseImg.addClass(" animated rotateIn fast");
    setTimeout(function () {
        reverse.css("display", "none");
    }, 1000);

    //current order
    if (globalCurrentOrder == "counterclockwise") {
        clockwise.css("display", "inline");
        counterclockwise.css("display", "none");
        globalCurrentOrder = "clockwise";
    } else {
        clockwise.css("display", "none");
        counterclockwise.css("display", "inline");
        globalCurrentOrder = "counterclockwise";
    }
}

/** wild change card effect **/
function wildChangeEffect() {
    // console.log("wildChangeEffect!");
    var changeColor = $('#changeColor');
    var changeColorImg = $('#changeColorImg');
    changeColor.css("display", "block");
    changeColorImg.addClass(" animated pulse faster");
    setTimeout(function () {
        changeColor.css("display", "none");
    }, 1000);
}

/** draw 2 or draw 4 card effect **/
function draw2OrDraw4Effect() {
    // console.log("drawCardEffect!");
    var drawCard = $('#drawCard');
    var drawCardImg = $('#drawCardImg');
    drawCard.css("display", "block");
    drawCardImg.addClass(" animated pulse faster");
    setTimeout(function () {
        drawCard.css("display", "none");
    }, 1000);
}

/** other player draw a card, display the effect **/
function updateDrawCard(data) {
    var curOrder = parseInt($('#curOrder').val());
    var relativeOrder = (parseInt(data['player']) - curOrder) % 4;
    if (relativeOrder < 0) {
        relativeOrder += 4;
    }
    drawCardEffectHelper(relativeOrder);
    var number = parseInt(data['number']);
    var waitTime = 0;
    while (number > 0) {
        setTimeout(function () {
            drawCardEffectHelper(relativeOrder);
        }, waitTime);
        waitTime = waitTime + 1000;
        number = number - 1;
    }
}

/** helper function to play other player's draw card effect **/
function drawCardEffectHelper(relativeOrder) {
    if (relativeOrder == 1) {
        playerDrawCardEffect('rightPlayerCards', "bounceInLeft");
        $('#rightPlayerUno').css("display", "none");
    } else if (relativeOrder == 2) {
        playerDrawCardEffect('topPlayerCards', "bounceInUp");
        $('#topPlayerUno').css("display", "none");
    } else if (relativeOrder == 3) {
        playerDrawCardEffect('leftPlayerCards', "bounceInRight");
        $('#leftPlayerUno').css("display", "none");
    }
}

/** current player draw a card, show the effect and put the new card into own cards **/
function drawCard(data) {
    document.getElementById('calledUNO').style.display = 'none';
    document.getElementById('unoButton').style.display = 'block';

    //reorganize own cards
    ownCards = $('#ownCards');
    ownCards.html("");
    document.getElementById('minEmptyIndex').value = 0;
    var cards = data['own_cards'];
    if (cards.length > 10) {
        $('#cardDistance').val("45");
    }
    for (var i = 0; i < cards.length; i++) {
        var isNew = false;
        for (var j = 0; j < data['added_cards'].length; j++) {
            if (data['added_cards'][j].id == cards[i].id) {
                isNew = true;
            }
        }
        if (isNew) {
            // console.log("new card:" + cards[i].color + "_" + cards[i].card_type);
            getOneCard(cards[i], "bounce");
        } else {
            getOneCard(cards[i], "");
        }
    }

}

/** current player play a card, show the effect **/
function playCard(data) {
    var ownCards = $('#ownCards');
    var playedCard = $('#' + data['card'].id);
    //remove the played card
    ownCards.remove(playedCard);
    //play card effect
    playCardEffect(data['card'].id, data['card'].color, data['card'].card_type,
        data['card'].img_src, "bounceInUp");
    document.getElementById("currentColor").removeAttribute("class");
    $('#currentColor').addClass(data['card'].color);
    globalCurrentColor = data['card'].color;
    //action card and wild card effect
    actionAndWildCardEffect(data['card'].card_type);
    //reorganize own cards
    ownCards.html("");
    document.getElementById('minEmptyIndex').value = 0;
    var cards = data['own_cards'];
    if (cards.length < 10) {
        $('#cardDistance').val("60");
    }
    for (var i = 0; i < cards.length; i++) {
        getOneCard(cards[i], "");
    }
    waitUNO = true;
    // console.log("waiting uno..");

    setTimeout(function () {
        waitUNO = false;
        // console.log("remove waiting uno..");
    }, 4000);
}

/** update other player's uno **/
function updateUno(data) {
    var curOrder = parseInt($('#curOrder').val());
    var relativeOrder = parseInt(data['player']) - curOrder;
    if (relativeOrder < 0) {
        relativeOrder += 4;
    }
    if (relativeOrder == 1) {
        $('#rightPlayerUno').css("display", "block");
    } else if (relativeOrder == 2) {
        $('#topPlayerUno').css("display", "block");
    } else if (relativeOrder == 3) {
        $('#leftPlayerUno').css("display", "block");
    }
}

/***************** websocket to consumer **********************/

/** get ready **/
$('#readyBtn').click(function (e) {
    e.preventDefault();
    addAnimate();
    setTimeout(function () {
        gameSocket.send(JSON.stringify({
            'action': 'getReady',
        }));

    }, 800);

});


/** play one card **/
function playOneCard(color, card_type, id) {
    // console.log("try to play card:" + color + "_" + card_type);
    //check whether your round
    if ($('#yourRound').css("display") == "block") {
        //check match current card
        // console.log(globalCurrentColor);
        var currentCardValue = document.getElementById('currentCard').value.split("_");
        if (color != globalCurrentColor && card_type != currentCardValue[2] && color != "wild")
            return;

        //if need to choose color,choose color
        if (card_type == "change" || card_type == "draw4") {
            layer.open({
                type: 2,
                title: 'chooseColor',
                closeBtn: 1,
                area: ['300px', '160px'],
                shade: 0.5,
                shadeClose: true,
                content: ['/game/chooseColor' + id],
            });
        } else {
            if ($('#yourRound').css("display") == "block") {
                // console.log("clearing timeout:" + timer);
                clearTimeout(timer);
                gameSocket.send(JSON.stringify({
                    'action': 'playOneCard',
                    'card_id': id,
                    'choose_color': "",
                }));
            }
        }
    }
}

/** helper function to play a card with chosen color **/
function playCardWithChosenColor(id, color) {
    if ($('#yourRound').css("display") == "block") {
        // console.log("clearing timeout:" + timer);
        clearTimeout(timer);
        gameSocket.send(JSON.stringify({
            'action': 'playOneCard',
            'card_id': id,
            'choose_color': color,
        }));
        document.getElementById("currentColor").removeAttribute("class");
        $('#currentColor').addClass(color);
    }
}

/** draw one card **/
$('#deckDiv').click(function (e) {
    if ($('#yourRound').css("display") == "block") {
        // console.log("clearing timeout:" + timer);
        clearTimeout(timer);
        gameSocket.send(JSON.stringify({
            'action': 'drawOneCard',
        }));
    }
});

/** call uno **/
function uno() {
    //check remain 1 card
    var ownCards = document.getElementById('ownCards');
    if (ownCards.childElementCount == 1 && waitUNO) {
        gameSocket.send(JSON.stringify({
            'action': 'callUno',
        }));
        document.getElementById('calledUNO').style.display = 'block';
        document.getElementById('unoButton').style.display = 'none';
    }

}

/** leave room **/
function leave() {
    if (started) {
        // gameSocket.send(JSON.stringify({
        //     'action': 'leaveGame',
        // }));
        window.location.pathname = '/';
    } else {
        window.location.pathname = '/';
    }
    // } else {
    //     var content = 'Are you sure you want to leave?<br> There will be a ' +
    //         '<strong style="font-size: 18px;color: orangered">50 points</strong>' +
    //         ' penalty!';
    //     $.confirm({
    //         theme: 'light',
    //         type: 'dark',
    //         typeAnimated: true,
    //         icon: 'glyphicon glyphicon-alert',
    //         closeIcon: true,
    //         title: 'Leaving Confirmation',
    //         content: content,
    //         buttons: {
    //             confirm: {
    //                 text: 'Leave Now',
    //                 btnClass: 'btn-default',
    //                 action: function () {
    //                     gameSocket.send(JSON.stringify({
    //                         'action': 'leaveGame',
    //                     }));
    //                     window.location.pathname = '/';
    //                 },
    //             },
    //             cancel: {
    //                 text: 'Stay',
    //                 btnClass: 'btn-blue',
    //                 action: function () {
    //                 },
    //             },

    //         }
    //     });
    // }
}

/** when click help button, show uno game rules **/
function showRules() {
    layer.open({
        type: 2,
        title: 'U Know Uno Rules',
        closeBtn: 1,
        area: ['400px', '600px'],
        shade: 0.5,
        shadeClose: true,
        content: ['/game/rules'],
    });
}

window.onbeforeunload = function (e) {
    if (started) {
        return '';
    }
}

window.onunload = function (e) {
    gameSocket.send(JSON.stringify({
        'action': 'leaveGame',
    }));
    window.location.pathname = '/';
}

gameSocket.onclose = function (e) {
    console.error('Game socket closed unexpectedly');
};