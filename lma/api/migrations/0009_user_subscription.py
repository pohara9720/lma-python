# Generated by Django 3.1.1 on 2020-09-24 17:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_auto_20200924_0238'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subscription',
            field=models.CharField(default='', max_length=75),
        ),
    ]