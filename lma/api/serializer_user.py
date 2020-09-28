from rest_framework import serializers
from .models import User
import serializer_company
import serializer_address


class UserSerializer(serializers.HyperlinkedModelSerializer):
    address = serializer_address.AddressSerializer()
    company = serializer_company.CompanySerializer()

    class Meta:
        model = User
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'role',
            'password',
            'address',
            'is_active',
            'company',
            # 'tasks'
        ]
