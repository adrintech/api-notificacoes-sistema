from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import viewsets
from .models import Notificacao
from .serializers import NotificacaoSerializer
from .motor import calcular_recomendacoes_fruki, obter_dados_externos_reais

class NotificacaoViewSet(viewsets.ModelViewSet):
    queryset = Notificacao.objects.all().order_by('-criada_em')
    serializer_class = NotificacaoSerializer

class MotorRecomendacaoAPIView(APIView):
    def get(self, request):
        # Simulando parâmetros que viriam do cliente/contexto
        tipo_mercado = request.GET.get('tipo_mercado', 'supermercado')

        # Dados reais de contexto (clima de Porto Alegre + feriado)
        contexto = obter_dados_externos_reais()
        temperatura = float(request.GET.get('temperatura', contexto['temperatura']))
        eh_feriado = contexto['eh_feriado']

        perfil = {"tipo": tipo_mercado}
        clima = {"temperatura": temperatura, "eh_feriado": eh_feriado}

        # Executa o motor de scoring
        sugestoes = calcular_recomendacoes_fruki(perfil, clima)

        return Response({
            "canal_alvo": "Pede Fruki (WhatsApp) / App Vendedor",
            "contexto_aplicado": {
                "perfil_mercado": tipo_mercado,
                "temperatura_atual": temperatura
            },
            "produtos_recomendados": sugestoes
        })