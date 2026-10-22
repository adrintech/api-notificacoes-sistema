from django.db import models

class Notificacao(models.Model):
    id_notificacao = models.AutoField(primary_key=True)
    cliente_id = models.IntegerField()
    tipo = models.CharField(max_length=100)
    mensagem = models.TextField()
    canal = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificacao_teste'
        managed = True 