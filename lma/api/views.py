from lma.utils import Util, Stripe
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication, TokenAuthentication
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework import permissions
from rest_framework import viewsets
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.decorators import action
from django.db.models import F

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
    BreedingSet
)
from .serializers import (
    UserSerializer,
    CompanySerializer,
    AddressSerializer,
    AnimalSerializer,
    InventorySerializer,
    InvoiceItemSerializer,
    SaleSerializer,
    TaskSerializer,
    ExpenseSerializer,
    BreedingSetSerializer
)


class VerifyEmail(APIView):
    def get(self, request):
        token = request.GET.get('token', '')
        user_email = Token.objects.get(key=token).user
        if user_email:
            User.objects.filter(email=user_email).update(is_active=True)
            return Response('Email Verified')
        else:
            return Response('No user with that token')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['post'])
    def get_active_user(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        user = Util.authenticate(request)
        return Response(user)

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        email = request.data['email']
        role = 'ADMIN'
        password = request.data['password']
        user_address = Util.save_address(
            request, 'street', 'state', 'city', 'zipcode'
        )
        company = Util.save_company(request)
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            address=user_address,
            company=company,
            is_active=True
        )
        user.set_password(password)
        user.save()
        serializer = UserSerializer(instance=user, context={
            'request': request})

        token = Token.objects.create(user=user).key
        current_site = get_current_site(request).domain
        link = reverse('verify-email')
        absurl = 'http://'+current_site+link+"?token="+token
        email_body = 'Hi '+user.first_name+' '+user.last_name + \
            ' Use the link below to verify your email \n' + absurl
        email_data = {'email_body': email_body, 'to_email': user.email,
                      'email_subject': 'Verify your email'}
        Util.send_email(email_data)

        return Response(serializer.data)

    @ action(detail=False, methods=['post'])
    def resend_email(self, request, pk=None):
        email = request.data['email']
        current_site = get_current_site(request).domain
        absurl = 'http://'+current_site+"/login"
        email_body = 'You have been invited to use Livestock Manager'
        ' Use the link below to login using your email as your email and password /n' + absurl
        email_data = {'email_body': email_body, 'to_email': email,
                      'email_subject': 'Please accept your invite'}
        Util.send_email(email_data)
        return Response('Email Sent')

    def create(self, request, authentication_classes=[TokenAuthentication]):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        current_site = get_current_site(request).domain
        absurl = 'http://'+current_site+"/login"
        email_body = 'Hello,'
        " You've been invited to use Livestock Manager. Please click the link to login using your email as your email and password. Password can be changed after in your profile \n" + absurl
        emails = request.data['emails']

        users = []
        for email in emails:
            user = User(email=email, role='USER',
                        company=company)
            user.set_password(email)
            user.save()
            serializer = UserSerializer(instance=user, context={
                'request': request})
            users.append(serializer.data)
            email_data = {'email_body': email_body, 'to_email': email,
                          'email_subject': "You've been invited to Livestock Manager"}
            Util.send_email(email_data)

        return Response(users)

    def list(self, request, authentication_classes=[TokenAuthentication]):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        serializer = CompanySerializer(instance=company, context={
            'request': request})
        return Response(serializer.data['users'])

    def partial_update(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        user = Util.authenticate(request)
        street = request.data['street']
        state = request.data['state']
        city = request.data['city']
        zipcode = request.data['zipcode']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        address_id = None
        if user['address'] is not None:
            address_id = user['address']['id']

        address, created = Address.objects.update_or_create(
            id=address_id, defaults={
                "street": street, "city": city, "state": state, "zipcode": zipcode
            }
        )
        updated = User.objects.filter(id=user['id']).update(
            first_name=first_name, last_name=last_name, address=address)
        return Response(updated)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    # permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'])
    def get_stripe_account(self, request, pk=None):
        user = Util.authenticate(request)
        if user['role'] == 'ADMIN':
            data = Stripe.retrieve_account(pk)
            return Response(data)

    @action(detail=True, methods=['post'])
    def update_stripe_account(self, request, pk=None):
        user = Util.authenticate(request)
        if user['role'] == 'ADMIN':
            data = Stripe.update_account(request, pk)
            return Response(data)

    def partial_update(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        user = Util.authenticate(request)
        data = request.data
        name = data['name']
        street = data['street']
        state = data['state']
        city = data['city']
        zipcode = data['zipcode']
        logo = Util.upload_file(data['logo'])
        address_id = user['company']['address']['id']
        if user['role'] == 'USER':  # TODO should be ADMIN
            Address.objects.filter(id=address_id).update(
                street=street, city=city, state=state, zipcode=zipcode
            )
            updated = Company.objects.filter(
                id=pk).update(name=name, logo=logo)
            return Response(updated)

        else:
            return Response('Unauthorized')


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    # permission_classes = [IsAuthenticated]


class BreedingSetViewSet(viewsets.ModelViewSet):
    queryset = BreedingSet.objects.all()
    serializer_class = BreedingSetSerializer
    # permission_classes = [IsAuthenticated]


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'])
    def get_pdf(self, request):
        table_data = Util.get_pdf_data(request, 'animal')
        pdf = Util.export_pdf(request, 'animals.pdf', table_data)
        return pdf

    @action(detail=True, methods=['post'])
    def get_tasks(self, request, pk=None):
        animal = Animal.objects.get(id=pk)
        tasks = animal.task_set.all()
        serializer = TaskSerializer(instance=tasks, context={
            'request': request}, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def get_parents(self, request, pk=None):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        type = request.data['type']
        males = ['BULL', 'STEER', 'WETHER', 'RAM',
                 'STUD', 'GELDING', 'BOAR', 'BARROW', 'BUCK']
        sires = []
        dams = []
        if type == 'N/A':
            animals = Animal.objects.filter(company=company_id)
            serializer = self.get_serializer(animals, many=True)
            for animal in serializer.data:
                if animal['sub_type'] in males:
                    sires.append(animal)
                else:
                    dams.append(animal)
            return Response({"father": sires, "mother": dams})
        else:
            animals = Animal.objects.filter(company=company_id, type=type)
            serializer = self.get_serializer(animals, many=True)
            for animal in serializer.data:
                if animal['sub_type'] in males:
                    sires.append(animal)
                else:
                    dams.append(animal)
            return Response({"father": sires, "mother": dams})

    @action(detail=False, methods=['post'])
    def get_offspring(self, request, pk=None):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        sub_type = request.data['sub_type']
        animal_id = request.data['id']
        males = ['BULL', 'STEER', 'WETHER', 'RAM',
                 'STUD', 'GELDING', 'BOAR', 'BARROW', 'BUCK']
        if sub_type in males:
            children = Animal.objects.filter(
                company=company_id, father=animal_id)
            serializer = self.get_serializer(children, many=True)
            return Response(serializer.data)
        else:
            children = Animal.objects.filter(
                company=company_id, mother=animal_id)
            serializer = self.get_serializer(children, many=True)
            return Response(serializer.data)

    def list(self, request):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        animals = Animal.objects.filter(company=company_id)
        page = self.paginate_queryset(animals)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(animals, many=True)
        return Response(serializer.data)

    def create(self, request):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        data = request.data
        header_image = Util.upload_file(data['header_image'])
        profile_image = Util.upload_file(data['profile_image'])
        attachment_file = data.get("attachment")
        attachment = None if attachment_file == None else Util.upload_file(
            attachment_file)
        new_animal = Animal.objects.create(
            name=data['name'],
            type=data['type'],
            sub_type=data['sub_type'],
            header_image=header_image,
            profile_image=profile_image,
            tag_number=data['tag_number'],
            registration_number=data['registration_number'],
            dob=data['dob'],
            father=data['father'],
            mother=data['mother'],
            attachment=attachment,
            company=company
        )
        serializer = self.get_serializer(new_animal)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        def serialize(animal_id):
            if animal_id == 'N/A':
                return animal_id
            else:
                animal = Animal.objects.get(id=animal_id)
                serializer = self.get_serializer(animal)
                return serializer.data

        primary = serialize(pk)
        primary['father'] = serialize(primary['father'])
        primary['mother'] = serialize(primary['mother'])
        return Response(primary)


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'])
    def get_pdf(self, request):
        table_data = Util.get_pdf_data(request, 'inventory')
        pdf = Util.export_pdf(request, 'inventory.pdf', table_data)
        return pdf

    @action(detail=False, methods=['post'])
    def get_breeding_sets(self, request, pk=None):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        animal_category = request.data['type']
        inventory = Inventory.objects.filter(
            company=company, animal_category=animal_category, category='SEMEN'
        )
        animals = Animal.objects.filter(company=company, type=animal_category)
        animal_serializer = AnimalSerializer(instance=animals, context={
                                             'request': request}, many=True)
        inventory_serializer = self.get_serializer(inventory, many=True)
        males_types = ['BULL', 'STEER', 'WETHER', 'RAM',
                       'STUD', 'GELDING', 'BOAR', 'BARROW', 'BUCK']
        males = []
        females = []
        for animal in animal_serializer.data:
            if animal['sub_type'] in males_types:
                males.append(animal)
            else:
                females.append(animal)
        for item in inventory_serializer.data:
            father = Animal.objects.get(id=item['father'])
            father_serializer = AnimalSerializer(instance=father, context={
                'request': request})
            item['father'] = father_serializer.data

        response = {
            "females": females,
            "semen": [*inventory_serializer.data, *males]
        }
        return Response(response)

    def list(self, request):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        inventory = Inventory.objects.filter(company=company)
        serializer = self.get_serializer(inventory, many=True)

        def get_parent(animal_id):
            if animal_id is not None:
                animal = Animal.objects.get(id=animal_id)
                parent_serializer = AnimalSerializer(instance=animal, context={
                    'request': request})
                return parent_serializer.data

        for item in serializer.data:
            item['father'] = get_parent(item.get('father'))
            item['mother'] = get_parent(item.get('mother'))
        return Response(serializer.data)

    def create(self, request, pk=None):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        data = request.data
        category = data['category']
        cost = data['cost']
        tank_number = data['tank_number']
        canister_number = data['canister_number']
        top_id = data['top_id']
        father = data.get('father')
        mother = data.get('mother')
        units = data['units']
        animal_category = data['animal_category']
        inventory = Inventory.objects.create(
            category=category,
            cost=cost,
            tank_number=tank_number,
            canister_number=canister_number,
            top_id=top_id,
            father=father,
            mother=mother,
            units=units,
            animal_category=animal_category,
            company=company
        )
        serializer = self.get_serializer(inventory)

        def get_parent(animal_id):
            if animal_id is not None:
                animal = Animal.objects.get(id=animal_id)
                parent_serializer = AnimalSerializer(instance=animal, context={
                    'request': request})
                return parent_serializer.data

        father_data = get_parent(father)
        mother_data = get_parent(mother)
        response = {
            **serializer.data,
            "father": father_data,
            "mother": mother_data
        }

        return Response(response)


class InvoiceItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    # permission_classes = [IsAuthenticated]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'])
    def get_pdf(self, request):
        table_data = Util.get_pdf_data(request, 'sale')
        pdf = Util.export_pdf(request, 'sales.pdf', table_data)
        return pdf

    def list(self, request):
        user = Util.authenticate(request)
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        sales = Sale.objects.filter(company=company)
        serializer = self.get_serializer(sales, many=True)
        return Response(serializer.data)

    def create(self, request):
        user = Util.authenticate(request)
        data = request.data
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        number = data['number']
        due_date = data['due_date']
        issue_date = data['issue_date']
        title = data['title']
        bill_to_name = data['bill_to_name']
        bill_to_address = data['bill_to_address']
        email = data['email']
        phone = data['phone']
        status = 'UNPAID'
        invoice_items = data['invoice_items']
        sale = Sale(
            number=number,
            due_date=due_date,
            issue_date=issue_date,
            title=title,
            bill_to_name=bill_to_name,
            bill_to_address=bill_to_address,
            phone=phone,
            email=email,
            status=status,
            company=company
        )
        sale.save()
        for item in invoice_items:
            cost = item['cost']
            description = item['description']
            quantity = item['quantity']
            if item['type'] == 'animal':
                animal = Animal.objects.get(id=item['item'])
                invoice_item = InvoiceItem(
                    type=item['type'],
                    cost=cost,
                    description=description,
                    quantity=quantity,
                    total_price=round(cost*quantity),
                    animal=animal,
                    sale=sale
                )
                invoice_item.save()
            else:
                inventory = Inventory.objects.get(id=item['item'])
                invoice_item = InvoiceItem(
                    type=item['type'],
                    cost=cost,
                    description=description,
                    quantity=quantity,
                    total_price=round(cost*quantity),
                    inventory=inventory,
                    sale=sale
                )
                invoice_item.save()
        email_body = 'Your invoice is below. '
        email_data = {'email_body': email_body, 'to_email': email,
                      'email_subject': 'You have been sent an invoice via Livestock Manager'}
        Util.send_email(email_data)
        serializer = self.get_serializer(sale)
        return Response(serializer.data)


class TaskViewset(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        task = Task.objects.filter(id=pk).update(completed=not(F('completed')))
        return Response(task)

    def list(self, request):
        user = Util.authenticate(request)
        role = user['role']
        if role == 'ADMIN':
            tasks = Task.objects.all()
            serializer = self.get_serializer(tasks, many=True)
            return Response(serializer.data)
        else:
            u = User.objects.get(id=user['id'])
            tasks = u.task_set.all()
            serializer = self.get_serializer(tasks, many=True)
            return Response(serializer.data)

    def create(self, request, pk=None):
        user = Util.authenticate(request)
        data = request.data
        company_id = user['company']['id']
        company = Company.objects.get(id=company_id)
        category = data['category']
        title = data['title']
        task_due_date = data['task_due_date']
        description = data['description']
        users = User.objects.filter(id__in=data['users'])
        if category == 'BREEDING':
            breeding_sets = []
            due_date = data['due_date']
            breeding = data['breeding']
            for selection in breeding:
                semen = selection['breeding_selection']
                female_id = selection['female_select']
                female = Animal.objects.get(id=female_id)
                if semen['type'] == 'animal':
                    animal = Animal.objects.get(id=semen['id'])
                    set = BreedingSet(
                        female=female,
                        animal_semen=animal
                    )

                    set.save()
                    breeding_sets.append(set)
                else:
                    inventory = Inventory.objects.get(id=semen['id'])
                    set = BreedingSet(
                        female=female,
                        inventory_semen=inventory
                    )
                    set.save()
                    breeding_sets.append(set)
            task = Task(
                title=title,
                category=category,
                task_due_date=task_due_date,
                due_date=due_date,
                description=description,
                company=company,
                completed=False
            )
            task.save()
            task.users.set(users)
            task.breeding_sets.set(breeding_sets)
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        else:
            animals = Animal.objects.filter(id__in=data['animals'])
            cost = data['cost']
            expense_per = round(cost / len(animals), 2)
            for a in animals:
                Expense.objects.create(cost=expense_per, animal=a)
            task = Task(
                title=title,
                category=category,
                task_due_date=task_due_date,
                description=description,
                company=company,
                completed=False
            )
            task.save()
            task.users.set(users)
            task.animals.set(animals)
            serializer = self.get_serializer(task)
            return Response(serializer.data)
