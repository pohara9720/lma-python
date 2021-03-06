import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from .managers import CustomUserManager
# Create your models here.


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    zipcode = models.IntegerField()


class Company(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    logo = models.CharField(max_length=100)
    subscription = models.CharField(max_length=20)
    payment_info = models.CharField(max_length=100)
    # Relationships
    address = models.OneToOneField(
        Address, default='', on_delete=models.CASCADE)
    # users = [User]
    # animals = [Animal]
    # inventory = [Inventory]
    # sales = [Sale]


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=15)
    email = models.EmailField(default="inactive@user.com", unique=True)
    # password = models.CharField(max_length=150)
    address = models.OneToOneField(
        Address, on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=False)
    # Relationships
    company = models.ForeignKey(
        Company, related_name='users', default='', on_delete=models.CASCADE, null=True)
    deleted = models.BooleanField(default=False)
    # Joined
    # tasks = [Task]
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.email


class Animal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    sub_type = models.CharField(max_length=50)
    header_image = models.CharField(max_length=150, null=True)
    profile_image = models.CharField(max_length=150, null=True)
    tag_number = models.CharField(max_length=50)
    registration_number = models.CharField(max_length=50)
    dob = models.DateField()
    breed = models.CharField(max_length=50)
    father = models.ForeignKey(
        'self', related_name='sire', default='', on_delete=models.CASCADE, null=True)
    mother = models.ForeignKey(
        'self', related_name='dam', default='', on_delete=models.CASCADE, null=True)
    father_placeholder = models.CharField(max_length=50, null=True)
    mother_placeholder = models.CharField(max_length=50, null=True)
    attachment = models.CharField(max_length=150, null=True)
    deleted = models.BooleanField(default=False)
    # Relationships
    company = models.ForeignKey(
        Company, related_name='animals', default='', on_delete=models.CASCADE
    )


class Inventory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(max_length=50)
    cost = models.IntegerField()
    tank_number = models.IntegerField()
    canister_number = models.IntegerField()
    top_id = models.IntegerField()
    deleted = models.BooleanField(default=False)
    father = models.ForeignKey(
        Animal, related_name='father_of', default='', on_delete=models.CASCADE, null=True
    )
    mother = models.ForeignKey(
        Animal, related_name='mother_of', default='', on_delete=models.CASCADE, null=True
    )
    units = models.IntegerField()
    animal_category = models.CharField(max_length=50, default='')
    # Relationships
    company = models.ForeignKey(
        Company, related_name='inventory', default='', on_delete=models.CASCADE
    )


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cost = models.IntegerField()
    # Relationships
    animal = models.ForeignKey(
        Animal, related_name='expenses', default='', on_delete=models.CASCADE
    )
    task_type = models.CharField(max_length=50, default='')


class BreedingSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    female = models.ForeignKey(
        Animal, related_name='mother_to', default='', on_delete=models.CASCADE
    )
    animal_semen = models.ForeignKey(
        Animal, related_name='father_to', default='', on_delete=models.CASCADE, null=True
    )
    inventory_semen = models.ForeignKey(
        Inventory, related_name='bred_with', default='', on_delete=models.CASCADE, null=True
    )


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=50)
    task_due_date = models.DateField()
    due_date = models.DateField(null=True)
    description = models.TextField(max_length=500)
    completed = models.BooleanField()
    deleted = models.BooleanField(default=False)
    # Relationships
    users = models.ManyToManyField(User)
    animals = models.ManyToManyField(Animal)
    cost = models.IntegerField(default=0)
    # expenses = models.ManyToManyField(Expense)
    breeding_sets = models.ManyToManyField(BreedingSet)
    company = models.ForeignKey(
        Company, related_name='tasks', default='', on_delete=models.CASCADE
    )


class Sale(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.IntegerField()
    due_date = models.DateField()
    issue_date = models.DateField()
    title = models.CharField(max_length=75)
    bill_to_name = models.CharField(max_length=75)
    bill_to_address = models.CharField(max_length=200)
    email = models.EmailField()
    status = models.CharField(max_length=50)
    phone = models.IntegerField()
    total = models.IntegerField(default=0)
    deleted = models.BooleanField(default=False)
    # Relationships
    company = models.ForeignKey(
        Company, related_name='sales', default='', on_delete=models.CASCADE)
    # Joined
    # items = [InvoiceItem]


class InvoiceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50)
    cost = models.IntegerField()
    quantity = models.IntegerField()
    total_price = models.IntegerField()
    description = models.CharField(max_length=150, default="")
    # Relationships
    inventory = models.ForeignKey(
        Inventory, related_name='invoice_items', default='', on_delete=models.CASCADE, null=True
    )
    animal = models.ForeignKey(
        Animal, related_name='invoice_items', default='', on_delete=models.CASCADE, null=True
    )
    sale = models.ForeignKey(Sale, related_name='items', default='',
                             on_delete=models.CASCADE)


class Transfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    accepted = models.BooleanField(default=False)
    transferred = models.BooleanField(default=False)
    created_by = models.EmailField(default='')
    email = models.EmailField()
    sale = models.ForeignKey(Sale, related_name='transfers', default='',
                             on_delete=models.CASCADE)
