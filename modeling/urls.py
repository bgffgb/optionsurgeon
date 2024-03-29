from django.urls import path
from modeling import views

urlpatterns = [
    path('sync', views.sync, name='sync'),
    path('update_portfolio', views.update_portfolio, name='update_portfolio'),
    path('update_chart', views.update_chart, name='update_chart'),
    path('modeling', views.modeling, name='modeling'),
    path('', views.redir, name='redir'),
]

