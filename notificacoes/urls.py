from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificacaoViewSet, MotorRecomendacaoAPIView, RecomendarLoteAPIView, pagina_pede_fruki

router = DefaultRouter()
router.register(r'notificacoes', NotificacaoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('recomendar/', MotorRecomendacaoAPIView.as_view(), name='motor-recomendar'),
    path('recomendar-lote/', RecomendarLoteAPIView.as_view(), name='motor-recomendar-lote'),
    path('tela/pede-fruki/', pagina_pede_fruki, name='tela-pede-fruki'),
]