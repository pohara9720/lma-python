# Generated by Django 3.1.1 on 2020-10-19 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_auto_20201014_2319'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='task_type',
            field=models.CharField(default='', max_length=50),
        ),
    ]
