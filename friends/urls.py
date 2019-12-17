from django.urls import path

from . import views

app_name='friends'
urlpatterns = [
    path('friendRequest/', views.friendRequest, name='friendRequest'),
    path('processFriendRequest/<uuid:uuid>', views.processFriendRequest, name='procesFriendRequest'),
    path('getProfile/', views.getProfile, name='getProfile')
]