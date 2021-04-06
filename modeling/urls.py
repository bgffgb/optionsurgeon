from django.urls import path
from modeling import views

urlpatterns = [
    path('modeling', views.modeling, name='modeling'),
]

