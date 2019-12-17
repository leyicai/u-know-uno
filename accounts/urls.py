from django.urls import path
from accounts import views

app_name = 'accounts'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile', views.profile, name='profile'),
    path('logout', views.logout, name='logout'),
    path('game_records', views.game_records, name='game_records'),
]
