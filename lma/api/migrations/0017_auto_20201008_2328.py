# Generated by Django 3.1.1 on 2020-10-08 23:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_remove_invoiceitem_item'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animal',
            name='attachment',
            field=models.CharField(max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='father',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='inventory',
            name='mother',
            field=models.CharField(max_length=50, null=True),
        ),
    ]
