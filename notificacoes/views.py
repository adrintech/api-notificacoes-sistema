from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import viewsets
from django.shortcuts import render
from django.db import transaction
import random

from .models import Notificacao
from .serializers import NotificacaoSerializer
from .motor import calcular_recomendacoes_fruki, obter_dados_externos_reais

STATUS_IGNORAR = ('pendente', 'enviada', 'lida')


class NotificacaoViewSet(viewsets.ModelViewSet):
    queryset = Notificacao.objects.all().order_by('-criada_em')
    serializer_class = NotificacaoSerializer

    @action(detail=True, methods=['patch'], url_path='atualizar-status')
    def atualizar_status(self, request, pk=None):
        """
        PATCH /api/notificacoes/<id>/atualizar-status/
        Body: {"status": "enviada" | "lida" | "erro" | "pendente"}
        """
        novo_status = request.data.get('status')
        status_validos = ['pendente', 'enviada', 'lida', 'erro']

        if not novo_status:
            return Response(
                {"erro": "Campo 'status' é obrigatório."},
                status=http_status.HTTP_400_BAD_REQUEST
            )
        if novo_status not in status_validos:
            return Response(
                {"erro": f"Status inválido. Valores aceitos: {', '.join(status_validos)}"},
                status=http_status.HTTP_400_BAD_REQUEST
            )

        try:
            notificacao = Notificacao.objects.get(pk=pk)
        except Notificacao.DoesNotExist:
            return Response(
                {"erro": f"Notificação {pk} não encontrada."},
                status=http_status.HTTP_404_NOT_FOUND
            )

        notificacao.status = novo_status
        notificacao.save(update_fields=['status'])

        return Response({
            "id_notificacao": notificacao.pk,
            "novo_status": novo_status,
            "atualizada_em": timezone.now().isoformat(),
        })


def pagina_pede_fruki(request):
    """Renderiza a interface visual do Pede Fruki (WhatsApp / App Vendedor)."""
    return render(request, 'notificacoes/pede_fruki.html')


class MotorRecomendacaoAPIView(APIView):
    def post(self, request):
        cliente_id = request.data.get('cliente_id')
        if cliente_id is None:
            return Response(
                {"erro": "Campo 'cliente_id' é obrigatório."},
                status=400
            )

        limite = int(request.data.get('limite', 3))

        try:
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT segmento FROM cliente WHERE id_cliente = %s",
                    [cliente_id]
                )
                row = cur.fetchone()
        except ObjectDoesNotExist:
            row = None

        if row is None:
            return Response(
                {"erro": f"Cliente {cliente_id} não encontrado no banco."},
                status=404
            )

        tipo_mercado = request.data.get('tipo_mercado') or (row[0] or 'supermercado').lower()

        contexto = obter_dados_externos_reais()
        temperatura = float(request.data.get('temperatura', contexto['temperatura']))
        eh_feriado = contexto['eh_feriado']

        perfil = {"tipo": tipo_mercado}
        clima = {"temperatura": temperatura, "eh_feriado": eh_feriado}

        sugestoes = calcular_recomendacoes_fruki(perfil, clima)[:limite]

        if not sugestoes:
            return Response({
                "cliente_id": cliente_id,
                "notificacoes_criadas": [],
                "mensagem": "Nenhum produto atingiu a pontuação mínima para este contexto."
            })

        notificacoes_criadas = []
        for sugestao in sugestoes:
            notificacao = Notificacao.objects.create(
                cliente_id=cliente_id,
                tipo="recomendacao_produto",
                mensagem=f"Sugestão para {tipo_mercado}: {sugestao['produto']} "
                         f"(score {sugestao['pontuacao']}). {sugestao['motivo']}.",
                canal="Pede Fruki (WhatsApp) / App Vendedor",
                status="pendente",
            )
            notificacoes_criadas.append(NotificacaoSerializer(notificacao).data)

        return Response({
            "cliente_id": cliente_id,
            "contexto_aplicado": {
                "perfil_mercado": tipo_mercado,
                "temperatura_atual": temperatura,
                "eh_feriado": eh_feriado,
            },
            "notificacoes_criadas": notificacoes_criadas,
        }, status=201)

    def get(self, request):
        cliente_id_param = request.GET.get('cliente_id')
        
        # Busca clientes reais do Supabase
        with connection.cursor() as cur:
            cur.execute("SELECT id_cliente, nome, segmento, subsegmento, cnpj FROM cliente")
            todos_clientes = cur.fetchall()

        if not todos_clientes:
            return Response({"erro": "Nenhum cliente encontrado no banco."}, status=404)

        # Seleciona o cliente (específico ou pega um aleatório do lote para demonstração)
        cliente_escolhido = None
        if cliente_id_param:
            for c in todos_clientes:
                if str(c[0]) == str(cliente_id_param):
                    cliente_escolhido = c
                    break
        
        if not cliente_escolhido:
            # Pega um aleatório (limitando a amostra para exibição dinâmica)
            amostra_clientes = random.sample(todos_clientes, min(50, len(todos_clientes)))
            cliente_escolhido = random.choice(amostra_clientes)
        else:
            amostra_clientes = random.sample(todos_clientes, min(50, len(todos_clientes)))

        id_cli, nome_cli, segmento_cli, subsegmento_cli, cnpj_cli = cliente_escolhido
        tipo_mercado = (segmento_cli or 'supermercado').lower()

        # Contexto real (Clima Open-Meteo + Feriado Nager.Date)
        contexto = obter_dados_externos_reais()
        temperatura = float(request.GET.get('temperatura', contexto['temperatura']))
        eh_feriado = contexto['eh_feriado']

        perfil = {"tipo": tipo_mercado}
        clima = {"temperatura": temperatura, "eh_feriado": eh_feriado}

        # Executa o motor de scoring
        sugestoes = calcular_recomendacoes_fruki(perfil, clima)

        return Response({
            "audit_motor": {
                "algoritmo": "Rule-Based Scoring & Contextual Filtering",
                "apis_externas": {
                    "clima": "Open-Meteo API (Porto Alegre/RS)",
                    "calendario": "Nager.Date Public Holidays API (Brasil)"
                },
                "temperatura_capturada": temperatura,
                "eh_feriado": eh_feriado
            },
            "cliente_analisado": {
                "id": id_cli,
                "nome": nome_cli,
                "cnpj": cnpj_cli,
                "segmento": segmento_cli,
                "subsegmento": subsegmento_cli
            },
            "amostra_total_clientes": len(todos_clientes),
            "ranking_produtos": sugestoes
        })


class RecomendarLoteAPIView(APIView):
    def post(self, request):
        segmento = request.data.get('segmento')
        limite = int(request.data.get('limite', 2))
        limite_clientes = int(request.data.get('limite_clientes', 100))

        contexto = obter_dados_externos_reais()
        temperatura = float(request.data.get('temperatura', contexto['temperatura']))
        eh_feriado = contexto['eh_feriado']
        clima = {"temperatura": temperatura, "eh_feriado": eh_feriado}

        clientes_qs = []
        with connection.cursor() as cur:
            if segmento:
                cur.execute(
                    """
                    SELECT c.id_cliente, c.segmento
                    FROM cliente c
                    WHERE LOWER(c.segmento) = LOWER(%s)
                      AND NOT EXISTS (
                          SELECT 1 FROM notificacao_teste n
                          WHERE n.cliente_id = c.id_cliente
                            AND n.status IN %s
                      )
                    LIMIT %s
                    """,
                    [segmento, tuple(STATUS_IGNORAR), limite_clientes]
                )
            else:
                cur.execute(
                    """
                    SELECT c.id_cliente, c.segmento
                    FROM cliente c
                    WHERE NOT EXISTS (
                        SELECT 1 FROM notificacao_teste n
                        WHERE n.cliente_id = c.id_cliente
                          AND n.status IN %s
                    )
                    LIMIT %s
                    """,
                    [tuple(STATUS_IGNORAR), limite_clientes]
                )
            clientes_qs = cur.fetchall()

        criadas = 0
        clientes_processados = 0
        clientes_sem_recomendacao = 0
        erros = []

        for id_cliente, segmento_cliente in clientes_qs:
            perfil = {"tipo": (segmento_cliente or 'supermercado').lower()}

            try:
                with transaction.atomic():
                    sugestoes = calcular_recomendacoes_fruki(perfil, clima)[:limite]
                    if not sugestoes:
                        clientes_sem_recomendacao += 1
                        continue

                    docs = [
                        Notificacao(
                            cliente_id=id_cliente,
                            tipo="recomendacao_produto",
                            mensagem=(
                                f"Sugestão para {perfil['tipo']}: "
                                f"{s['produto']} (score {s['pontuacao']}). {s['motivo']}."
                            ),
                            canal="Pede Fruki (WhatsApp) / App Vendedor",
                            status="pendente",
                        )
                        for s in sugestoes
                    ]
                    Notificacao.objects.bulk_create(docs)
                    criadas += len(docs)
                    clientes_processados += 1
            except Exception as e:
                erros.append({"cliente_id": id_cliente, "erro": str(e)})

        return Response({
            "contexto": {"temperatura": temperatura, "eh_feriado": eh_feriado},
            "segmento_filtrado": segmento,
            "clientes_candidatos": len(clientes_qs),
            "clientes_processados": clientes_processados,
            "clientes_sem_recomendacao": clientes_sem_recomendacao,
            "notificacoes_criadas": criadas,
            "erros": erros,
        })