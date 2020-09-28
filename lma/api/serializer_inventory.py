from rest_framework import serializers
from .models import Inventory
import serializer_company


class InventorySerializer(serializers.HyperlinkedModelSerializer):
    company = serializer_company.CompanySerializer()

    class Meta:
        model = Inventory
        fields = [
            'id',
            'category',
            'cost',
            'tank_number',
            'canister_number',
            'top_id',
            'father',
            'mother',
            'units',
            'company'
        ]
