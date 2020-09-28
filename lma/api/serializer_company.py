from rest_framework import serializers
from .models import Company
import serializer_address
import serializer_user
import serializer_animal
import serializer_sale
import serializer_inventory


class CompanySerializer(serializers.HyperlinkedModelSerializer):
    address = serializer_address.AddressSerializer(read_only=True)
    users = serializer_user.UserSerializer(many=True)
    animals = serializer_animal.AnimalSerializer(many=True)
    inventory = serializer_inventory.InventorySerializer(many=True)
    sales = serializer_sale.SaleSerializer(many=True)

    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'email',
            'logo',
            'membership',
            'payment_info',
            'address',
            'users',
            'animals',
            'inventory',
            'sales'
        ]
