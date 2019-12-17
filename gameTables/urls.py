from . import views
from django.conf.urls import url
from django.urls import path

app_name = 'gameTables'
urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    path('reload_if_necessary/', views.reload_if_necessary, name='reload_if_necessary'),
]
