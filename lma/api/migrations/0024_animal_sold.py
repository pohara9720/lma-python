# Generated by Django 3.1.1 on 2020-10-20 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_expense_task_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='animal',
            name='sold',
            field=models.BooleanField(default=False),
        ),
    ]