from rest_framework import serializers
from .models import InvoiceItem
import serializer_sale


class InvoiceItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'type',
            'item',
            'quantity',
            'total_price',
            'description',
            'sale',
            'cost'
        ]
