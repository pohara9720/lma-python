# Generated by Django 3.1.1 on 2020-10-30 02:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_auto_20201030_0047'),
    ]

    operations = [
        migrations.AddField(
            model_name='transfer',
            name='created_by',
            field=models.EmailField(default='', max_length=254),
        ),
    ]