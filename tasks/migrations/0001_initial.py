# Generated by Django 5.2.1 on 2025-06-05 05:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Administrador',
            fields=[
                ('carnet_admin', models.CharField(max_length=8, primary_key=True, serialize=False)),
                ('password_admin', models.CharField(max_length=15)),
                ('nombre_admin', models.CharField(max_length=30)),
            ],
            options={
                'db_table': 'administrador',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Buque',
            fields=[
                ('matricula_buque', models.CharField(max_length=7, primary_key=True, serialize=False)),
                ('servicio', models.CharField(max_length=30)),
                ('nombre_buque', models.CharField(max_length=25)),
            ],
            options={
                'db_table': 'buque',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Gerente',
            fields=[
                ('carnet_gerente', models.CharField(max_length=8, primary_key=True, serialize=False)),
                ('nombre_gerente', models.CharField(max_length=50)),
                ('password_gerente', models.CharField(max_length=15)),
                ('email', models.CharField(max_length=30)),
            ],
            options={
                'db_table': 'gerente',
                'managed': False,
            },
        ),
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('codigo_producto', models.CharField(max_length=15, primary_key=True, serialize=False)),
                ('nombre_producto', models.CharField(max_length=25)),
                ('descripcion', models.CharField(max_length=100)),
                ('foto_producto', models.ImageField(blank=True, null=True, upload_to='media/')),
                ('cantidad', models.IntegerField(default=0)),
                ('stock_minimo', models.IntegerField()),
                ('tipo', models.CharField(max_length=10)),
                ('fecha_caducidad', models.DateField(blank=True, null=True)),
                ('carnet_admin', models.ForeignKey(blank=True, db_column='carnet_admin', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='tasks.administrador')),
                ('matricula_buque', models.ForeignKey(blank=True, db_column='matricula_buque', null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='tasks.buque')),
            ],
            options={
                'db_table': 'producto',
                'managed': True,
            },
        ),
    ]
