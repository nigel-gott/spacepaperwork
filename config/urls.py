"""goldengoose URL Configuration
"""
import debug_toolbar
from django.contrib import admin
from django.urls import path
from django.conf.urls import include, url

urlpatterns = [
    url(r'^goosetools/', include([
        path('admin/', admin.site.urls),
        path('', include('core.urls')),  
        path('accounts/', include('allauth.urls')),
        path('__debug__/', include(debug_toolbar.urls)),
    ])),
]
