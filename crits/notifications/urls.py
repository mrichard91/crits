from django.urls import re_path as url

from . import views

urlpatterns = [
    url(r'^poll/$', views.poll, name='crits-notifications-views-poll'),
    url(r'^ack/$', views.acknowledge, name='crits-notifications-views-acknowledge'),
]
