from rest_framework import serializers
from .models import Sale
import serializer_company
import serializer_invoice_item


class SaleSerializer(serializers.HyperlinkedModelSerializer):
    items = serializer_invoice_item.InvoiceItemSerializer(many=True)
    company = serializer_company.CompanySerializer()

    class Meta:
        model = Sale
        fields = [
            'id',
            'number',
            'due_date',
            'issue_date',
            'title',
            'bill_to_name',
            'bill_to_address',
            'email',
            'status',
            'phone',
            'company',
            'items'
        ]
