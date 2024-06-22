from django.contrib import admin
from django.urls import path, include
from rest_framework import viewsets, response


class HealthCheckView(viewsets.ViewSet):
    def list(self):
        return response.Response({'status': 'ok'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.urls')),
    path('healthcheck/', HealthCheckView.as_view({'get': 'list'}), name='healthcheck')
]
