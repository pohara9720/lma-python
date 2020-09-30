from rest_framework import serializers
from .models import (
    User,
    Company,
    Address,
    Animal,
    Inventory,
    Task,
    InvoiceItem,
    Sale,
    Expense
)


class AddressSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id',
            'street',
            'city',
            'state',
            'zipcode'
        ]


class UserSerializer(serializers.HyperlinkedModelSerializer):
    address = AddressSerializer()

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
        ]


class ExpenseSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Expense
        fields = [
            'id',
            'cost',
            'animal'
        ]


class AnimalSerializer(serializers.HyperlinkedModelSerializer):
    # expenses = ExpenseSerializer(many=True)

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
            'company',
            'expenses'
        ]


class InventorySerializer(serializers.HyperlinkedModelSerializer):
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
            'company',
            'tasks',
            'invoice_items'
        ]


class InvoiceItemSerializer(serializers.HyperlinkedModelSerializer):
    # inventory = InventorySerializer()

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
            'cost',
            'inventory'
        ]


class SaleSerializer(serializers.HyperlinkedModelSerializer):
    # items = InvoiceItemSerializer(many=True)

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


class TaskSerializer(serializers.HyperlinkedModelSerializer):
    # users = UserSerializer(many=True)
    # animals = AnimalSerializer(many=True)
    # expenses = ExpenseSerializer(many=True)
    # inventory = InventorySerializer()

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'category',
            'assigned_date',
            'due_date',
            'description',
            'completed',
            'users',
            'animals',
            'expenses',
            'inventory',
            'company'
        ]


class CompanySerializer(serializers.HyperlinkedModelSerializer):
    address = AddressSerializer()
    users = UserSerializer(many=True)
    # animals = AnimalSerializer(many=True)
    # inventory = InventorySerializer(many=True)
    # sales = SaleSerializer(many=True)
    # tasks = TaskSerializer(many=True)

    class Meta:
        model = Company
        fields = [
            'id',
            'name',
            'email',
            'logo',
            'subscription',
            'payment_info',
            'address',
            'users',
            'animals',
            'inventory',
            'sales',
            'tasks'
        ]
