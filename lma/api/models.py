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
        Company, related_name='users', default='', on_delete=models.CASCADE)
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
    header_image = models.CharField(max_length=150)
    profile_image = models.CharField(max_length=150)
    tag_number = models.CharField(max_length=50)
    registration_number = models.CharField(max_length=50)
    dob = models.DateField()
    breed = models.CharField(max_length=50)
    father = models.CharField(max_length=50)
    mother = models.CharField(max_length=50)
    attachment = models.CharField(max_length=150)
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
    father = models.CharField(max_length=50)
    mother = models.CharField(max_length=50)
    units = models.IntegerField()
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


class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=50)
    assigned_date = models.DateField()
    due_date = models.DateField()
    description = models.TextField(max_length=500)
    completed = models.BooleanField()
    # Relationships
    users = models.ManyToManyField(User)
    animals = models.ManyToManyField(Animal)
    cost = models.IntegerField(default=0)
    expenses = models.ManyToManyField(Expense)
    inventory = models.ForeignKey(
        Inventory, related_name='tasks', default='', on_delete=models.CASCADE
    )
    company = models.ForeignKey(
        Company, related_name='tasks', default='', on_delete=models.CASCADE)


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
    # Relationships
    company = models.ForeignKey(
        Company, related_name='sales', default='', on_delete=models.CASCADE)
    # Joined
    # items = [InvoiceItem]


class InvoiceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=50)
    item = models.CharField(max_length=150)
    cost = models.IntegerField()
    quantity = models.IntegerField()
    total_price = models.IntegerField()
    description = models.CharField(max_length=150, default="")
    # Relationships
    inventory = models.ForeignKey(
        Inventory, related_name='invoice_items', default='', on_delete=models.CASCADE
    )
    sale = models.ForeignKey(Sale, related_name='items', default='',
                             on_delete=models.CASCADE)
