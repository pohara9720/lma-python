# Generated by Django 3.1.1 on 2020-10-14 23:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_auto_20201014_2141'),
    ]

    operations = [
        migrations.AlterField(
            model_name='animal',
            name='father',
            field=models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sire', to='api.animal'),
        ),
        migrations.AlterField(
            model_name='animal',
            name='mother',
            field=models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dam', to='api.animal'),
        ),
    ]
