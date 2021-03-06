# Generated by Django 3.1.1 on 2020-10-05 21:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_auto_20201005_2147'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceitem',
            name='inventory',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE, related_name='invoice_items', to='api.inventory'),
        ),
        migrations.AlterField(
            model_name='task',
            name='inventory',
            field=models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='api.inventory'),
        ),
    ]
