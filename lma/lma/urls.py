"""lma URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path
from rest_framework import routers
from api import views
from django.conf.urls import url
from api.view_auth_token import AuthTokenView

router = routers.DefaultRouter()
router.register(r'user', views.UserViewSet, 'user')
router.register(r'company', views.CompanyViewSet, 'company')
router.register(r'address', views.AddressViewSet, 'address')
router.register(r'animal', views.AnimalViewSet, 'animal')
router.register(r'inventory', views.InventoryViewSet, 'inventory')
router.register(r'item', views.InvoiceItemViewSet, 'item')
router.register(r'sale', views.SaleViewSet, 'sale')
router.register(r'task', views.TaskViewset, 'task')
router.register(r'breedingset', views.BreedingSetViewSet, 'breedingset')
# router.register(r'register', views.RegisterView.as_view(), basename='register')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # path('api-token-auth/', token_view.obtain_auth_token, name='api-token-auth')
    # url(r'api-token-auth/', views.Authenticate.as_view())
    url(r'^api-token-auth/', AuthTokenView.as_view()),
    path('verify-email/', views.VerifyEmail.as_view(), name='verify-email'),
    # url(r'register/', views.RegisterView.as_view(), name='register'),
]
