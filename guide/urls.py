from django.urls import path
from guide import views

urlpatterns = [
    path('guide', views.tutorial, name='tutorial'),
    path('rnd', views.rnd, name='rnd')
]
