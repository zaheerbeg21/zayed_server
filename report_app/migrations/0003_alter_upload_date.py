# Generated by Django 3.2.13 on 2022-07-21 10:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('report_app', '0002_alter_upload_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upload',
            name='date',
            field=models.DateTimeField(null=True),
        ),
    ]
