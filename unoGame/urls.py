from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'unoGame'
urlpatterns = [
    path('create/', views.createGame, name='createGame'),
    path('<int:game_id>/', views.inGame, name='inGame'),
    # path('<int:game_id>/', views.startGame, name='startGame'),
    path('<int:game_id>/beforeGameAuth/',
         views.beforeGameAuth, name='beforeGameAuth'),
    path('<int:game_id>/end/', views.endGame, name='endGame'),
    # path('<int:game_id>/lose/', views.lose, name='lose'),
    path('<int:game_id>/generatePassword/',
         views.generatePassword, name='generatePassword'),
    path('<int:game_id>/beforeGameAuth/validatePassword/',
         views.validatePassword, name='validatePassword'),
    url(r'chooseColor(\d+)', views.chooseColor, name='chooseColor'),
    url(r'rules', views.showRules, name='rules'),

]
