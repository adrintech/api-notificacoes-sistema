from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificacaoViewSet, MotorRecomendacaoAPIView

router = DefaultRouter()
router.register(r'notificacoes', NotificacaoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('recomendar/', MotorRecomendacaoAPIView.as_view(), name='motor-recomendar'),
]