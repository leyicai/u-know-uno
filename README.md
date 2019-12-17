# U Know UNO
This the course project of course 17637 - WebApps, Fall 2019 at Carnegie Mellon University.

**Authors:**
- Anthony Attipoe
- Leyi Cai
- Ruihan Feng
- Yichen Liu

## Introduction

*U Know Uno* is an online game platform of UNO game. It has provided the following functions:

- Logged-in users can play UNO games with each other in four-players mode. Computer players will be automatically added to a game if less than 4 people start the game.
- Users can chat with each other in the Game Lobby or in a certain game room.
- Users can create game rooms and make them private by generating random passwords. The passwords will be used for other users to enter the private game rooms.
- Users can send friend requests and game invitations to each other via emails.

## Requirements
- Python 3 or above
- Django 2.2.x
- docker

## Usage
To run this django project locally:
```bash
# activate virtual environment
source venv/bin/activate
# install requirements
pip install -r requirements.txt
# start docker for the channels
docker run -p 6379:6379 -d redis:2.8
# get into the project directory where the manage.py is
cd UKnowUNO/
# run
python manage.py runserver
```
Deactivate virtual environment after usage:
```bash
deactivate
```
## Deployment

This project has been deployed on Heroku. 

[Check it out!](https://u-know-uno.herokuapp.com/)

## External Resources

- Images used in this project are obtained (and possibly modified) from the following sites:
    * https://genslerzudansdentistry.com/about-us/anonymous-user/
    * https://en.wikipedia.org/wiki/Uno_(card_game)
    - http://unocardinfo.victorhomedia.com/
- [Animate.css](https://daneden.github.io/animate.css/)
- [Materialize](https://materializecss.com/)
- [jQuery](https://code.jquery.com/)
- [Bootstrap](https://getbootstrap.com/)

## Reference

- For game consumers: https://github.com/aduranil/django-channels-react-multiplayer
- For django channels: https://blog.heroku.com/in_deep_with_django_channels_the_future_of_real_time_apps_in_django
- Uno game: https://github.com/bennuttall/uno/blob/master/uno.py
