from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView

def health(request):
    return JsonResponse({'status':'ok','message':'Pokemon Nexus Django JWT Backend is running'})

urlpatterns = [
    path('', health),
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
