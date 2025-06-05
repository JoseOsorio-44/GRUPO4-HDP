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
    codigo_producto = models.CharField(primary_key=True, max_length=15) 
    matricula_buque = models.ForeignKey(Buque, models.DO_NOTHING, db_column='matricula_buque', blank=True, null=True)
    carnet_admin = models.ForeignKey(Administrador, models.DO_NOTHING, db_column='carnet_admin', blank=True, null=True) # O carnet_gerente si era el caso
    nombre_producto = models.CharField(max_length=25)
    descripcion = models.CharField(max_length=100)
    foto_producto = models.ImageField(upload_to='media/', blank=True, null=True) 
    cantidad = models.IntegerField(default=0) 
    stock_minimo = models.IntegerField()
    tipo = models.CharField(max_length=10)
    fecha_caducidad = models.DateField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'producto'
