from django.db import models


class Administrador(models.Model):
    carnet_admin = models.CharField(primary_key=True, max_length=8)
    password_admin = models.CharField(max_length=15)
    nombre_admin = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'administrador'

class Buque(models.Model):
    matricula_buque = models.CharField(primary_key=True, max_length=7)
    carnet_gerente = models.ForeignKey('Gerente', models.DO_NOTHING, db_column='carnet_gerente', blank=True, null=True)
    carnet_admin = models.ForeignKey(Administrador, models.DO_NOTHING, db_column='carnet_admin', blank=True, null=True)
    servicio = models.CharField(max_length=30)
    nombre_buque = models.CharField(max_length=25)

    class Meta:
        managed = False
        db_table = 'buque'


class Gerente(models.Model):
    carnet_gerente = models.CharField(primary_key=True, max_length=8)
    matricula_buque = models.ForeignKey(Buque, models.DO_NOTHING, db_column='matricula_buque', blank=True, null=True)
    nombre_gerente = models.CharField(max_length=50)
    password_gerente = models.CharField(max_length=15)
    email = models.CharField(max_length=30)

    class Meta:
        managed = False
        db_table = 'gerente'


class Producto(models.Model):
    id_producto = models.IntegerField(primary_key=True)
    matricula_buque = models.ForeignKey(Buque, models.DO_NOTHING, db_column='matricula_buque', blank=True, null=True)
    carnet_gerente = models.ForeignKey(Gerente, models.DO_NOTHING, db_column='carnet_gerente', blank=True, null=True)
    carnet_admin = models.ForeignKey(Administrador, models.DO_NOTHING, db_column='carnet_admin', blank=True, null=True)
    nombre_producto = models.CharField(max_length=25)
    descripcion = models.CharField(max_length=100)
    foto_producto = models.CharField(max_length=254)
    stock_minimo = models.IntegerField()
    tipo = models.CharField(max_length=3)

    class Meta:
        managed = False
        db_table = 'producto'