# Generated by Django 3.2.13 on 2022-07-21 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upload',
            name='date',
            field=models.DateTimeField(),
        ),
    ]
