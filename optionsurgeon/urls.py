from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('modeling.urls')),
    path('', include('guide.urls')),
    path('', include('contact.urls')),
]
