from django.db import models

# Create your models here.
class Administrador(models.Model):
    id_administrador = models.IntegerField(primary_key=True)
    identificador_admi = models.CharField(max_length=8)
    contrasenia_admi = models.CharField(max_length=15)

    class Meta:
        managed = False
        db_table = 'administrador'
        
    def __str__(self):
        return f"Admin {self.id_administrador}" 


class Buque(models.Model):
    id_buque = models.IntegerField(primary_key=True)
    id_gerente = models.ForeignKey('Gerente', models.DO_NOTHING, db_column='id_gerente', blank=True, null=True)
    id_administrador = models.ForeignKey(Administrador, models.DO_NOTHING, db_column='id_administrador', blank=True, null=True)
    nombre_buque = models.CharField(max_length=25)
    matricula = models.CharField(max_length=7)
    servicio = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'buque'


class Gerente(models.Model):
    id_gerente = models.IntegerField(primary_key=True)
    id_buque = models.ForeignKey(Buque, models.DO_NOTHING, db_column='id_buque', blank=True, null=True)
    identificador_gerente = models.CharField(max_length=8)
    nombre_gerente = models.CharField(max_length=50)
    contrasenia_gerente = models.CharField(max_length=15)
    email = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'gerente'


class Producto(models.Model):
    id_buque = models.ForeignKey(Buque, models.DO_NOTHING, db_column='id_buque', blank=True, null=True)
    id_gerente = models.ForeignKey(Gerente, models.DO_NOTHING, db_column='id_gerente', blank=True, null=True)
    id_administrador = models.ForeignKey(Administrador, models.DO_NOTHING, db_column='id_administrador', blank=True, null=True)
    nombre_producto = models.CharField(max_length=25)
    descripcion = models.CharField(max_length=100)
    foto_producto = models.CharField(max_length=254)
    stock_minimo = models.IntegerField()
    tipo = models.CharField(max_length=3)

    class Meta:
        managed = False
        db_table = 'producto'
