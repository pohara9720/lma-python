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
    Expense,
    BreedingSet,
    Transfer
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

# TODO DONT DO THIS!!!


class TodoRemoveSerializer(serializers.HyperlinkedModelSerializer):
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
            'deleted'
        ]


class TodoRemoveSerializer2(serializers.HyperlinkedModelSerializer):
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
            'deleted'
        ]


class TodoRemoveSerializer3(serializers.HyperlinkedModelSerializer):
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
            'items',
            'total',
            'deleted'
        ]


class ExpenseSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Expense
        fields = [
            'id',
            'cost',
            'animal',
            'task_type'
        ]


class AnimalSerializer(serializers.HyperlinkedModelSerializer):
    expenses = ExpenseSerializer(many=True)

    class Meta:
        model = Animal
        fields = [
            'id',
            'name',
            'type',
            'breed',
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
            'expenses',
            'mother_to',
            'father_to',
            'sire',
            'dam',
            'father_placeholder',
            'mother_placeholder',
            'deleted'
        ]

    def get_fields(self):
        fields = super(AnimalSerializer, self).get_fields()
        fields['father'] = AnimalSerializer()
        fields['mother'] = AnimalSerializer()
        return fields


class InventorySerializer(serializers.HyperlinkedModelSerializer):
    father = AnimalSerializer()
    mother = AnimalSerializer()

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
            'invoice_items',
            'animal_category',
            'bred_with',
            'deleted'
        ]


class InvoiceItemSerializer(serializers.HyperlinkedModelSerializer):
    inventory = InventorySerializer()
    animal = AnimalSerializer()
    sale = TodoRemoveSerializer3()

    class Meta:
        model = InvoiceItem
        fields = [
            'id',
            'type',
            'quantity',
            'total_price',
            'description',
            'sale',
            'cost',
            'inventory',
            'animal'
        ]


class BreedingSetSerializer(serializers.HyperlinkedModelSerializer):
    female = AnimalSerializer()
    animal_semen = AnimalSerializer()
    inventory_semen = InventorySerializer()

    class Meta:
        model = BreedingSet
        fields = [
            'id',
            'female',
            'animal_semen',
            'inventory_semen'
        ]


class SaleSerializer(serializers.HyperlinkedModelSerializer):
    items = InvoiceItemSerializer(many=True)

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
            'items',
            'total',
            'deleted'
        ]


class TransferSerializer(serializers.HyperlinkedModelSerializer):
    sale = SaleSerializer()

    class Meta:
        model = Transfer
        fields = [
            'id',
            'sale',
            'accepted',
            'transferred',
            'email',
            'created_by'
        ]


class TaskSerializer(serializers.HyperlinkedModelSerializer):
    users = TodoRemoveSerializer2(many=True)
    animals = AnimalSerializer(many=True)
    breeding_sets = BreedingSetSerializer(many=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'title',
            'category',
            'task_due_date',
            'due_date',
            'description',
            'completed',
            'users',
            'animals',
            'cost',
            'deleted',
            'breeding_sets',
            'company'
        ]


class CompanySerializer(serializers.HyperlinkedModelSerializer):
    address = AddressSerializer()
    users = TodoRemoveSerializer(many=True)
    animals = AnimalSerializer(many=True)
    inventory = InventorySerializer(many=True)
    # sales = SaleSerializer(many=True)
    tasks = TaskSerializer(many=True)

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


class UserSerializer(serializers.HyperlinkedModelSerializer):
    address = AddressSerializer()
    company = CompanySerializer()

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
            'deleted'
        ]
