from rest_framework import serializers
from .models import Animal
import serializer_company


class AnimalSerializer(serializers.HyperlinkedModelSerializer):
    company = serializer_company.CompanySerializer()

    class Meta:
        model = Animal
        fields = [
            'id',
            'name',
            'type',
            'sub_type',
            'header_image',
            'profile_image',
            'tag_number',
            'registration_number',
            'dob',
            'father',
            'mother',
            'attachment',
            'company'
        ]
