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
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.decorators import action
from django.db.models import F, Q
import datetime
from json import loads, dumps
from django.http import HttpResponseServerError
import secrets
import string

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
    BreedingSetSerializer,
    TransferSerializer
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

    @action(detail=True, methods=['get'], authentication_classes=[TokenAuthentication])
    def retrieve_subscription(self, request, pk=None):
        try:
            sub = Stripe.retrieve_subscription(pk)
            return Response(sub)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'])
    def forgot_password(self, request, pk=None):
        try:
            email = request.data['email']
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet)
                                    for i in range(20))
            user = User.objects.get(email=email)
            user.set_password(temp_password)
            user.save()
            email_body = 'Hello please use this temporary password to login. You may change it in your profile secion once authenticated ' + temp_password
            email_data = {'email_body': email_body, 'to_email': [email],
                          'email_subject': 'Temporary Password Request'}
            Util.send_email(email_data)
            return Response({'status': 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def change_password(self, request, pk=None):
        try:
            user = Util.authenticate(request, True)
            password = request.data['password']
            user.set_password(password)
            user.save()
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def get_active_user(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            return Response(user)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def update_subscription(self, request, pk=None):
        try:
            price_id = request.data['price']
            sub_id = request.data['id']
            updated = Stripe.update_subscription(sub_id, price_id)
            return Response(updated)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        email = request.data['email']
        try:
            transfer = Transfer.objects.get(email=email)
        except Transfer.DoesNotExist:
            transfer = None
        try:
            first_name = request.data['first_name']
            last_name = request.data['last_name']
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
            )
            user.set_password(password)
            user.save()
            if transfer is not None and transfer.accepted:
                items = InvoiceItem.objects.filter(sale=transfer.sale)
                for item in items:
                    animal = item.animal
                    inventory = item.inventory
                    if animal is not None:
                        animal.company = company
                        animal.save()
                    if inventory is not None:
                        u = inventory.units
                        q = item.quantity
                        is_all = u - q <= 0
                        if is_all:
                            inventory.company = company
                            inventory.save()
                        else:
                            copy = Inventory.objects.get(id=inventory.id)
                            copy.id = None
                            copy.company = company
                            copy.units = item.quantity
                            inventory.units = inventory.units - item.quantity
                            copy.save()
                            inventory.save()
                transfer.transferred = True
                transfer.save()
            serializer = UserSerializer(instance=user, context={
                'request': request})
            token = Token.objects.create(user=user).key
            url = settings.REACT_DOMAIN+'verify-email/'+token
            email_body = 'Hi '+user.first_name+' '+user.last_name + \
                ' Use the link below to verify your email \n' + url
            email_data = {'email_body': email_body, 'to_email': [user.email],
                          'email_subject': 'Verify your email'}
            Util.send_email(email_data)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'])
    def resend_email(self, request, pk=None):
        try:
            activation = request.data.get('activation')
            email = request.data['email']
            if activation is not None:
                user = User.objects.get(email=email)
                token = Token.objects.get(user=user).key
                url = settings.REACT_DOMAIN+'verify-email/'+token
                email_body = 'Hi '+user.first_name+' '+user.last_name + \
                    ' Use the link below to verify your email \n' + url
                email_data = {'email_body': email_body, 'to_email': [user.email],
                              'email_subject': 'Verify your email'}
                Util.send_email(email_data)
                return Response('Email Sent')
            else:
                url = settings.REACT_DOMAIN+'login'
                email_body = 'You have been invited to use Livestock Manager. Use the link below to login using your email as your email and password ' + url
                email_data = {'email_body': email_body, 'to_email': [email],
                              'email_subject': 'Please accept your invite'}
                Util.send_email(email_data)
                return Response('Email Sent')
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def search(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            value = request.data['value']
            users = User.objects.filter(
                Q(
                    first_name__icontains=value, company=company, deleted=False
                ) | Q(
                    last_name__icontains=value, company=company, deleted=False
                )
            )
            page = self.paginate_queryset(users)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(users, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['post'], authentication_classes=[TokenAuthentication])
    def delete_single(self, request, pk=None):
        try:
            user = User.objects.get(id=pk)
            user.deleted = True
            user.save()
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def batch_delete(self, request, pk=None):
        try:
            users = request.data['users']
            for user in User.objects.filter(id__in=users):
                user.deleted = True
                user.save()
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def create(self, request, authentication_classes=[TokenAuthentication]):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            url = settings.REACT_DOMAIN + 'login'
            emails = request.data['emails']
            email_body = "Hello, You've been invited to use Livestock Manager. Please click the link to login using your email as your email and password. Password can be changed after in your profile " + url
            email_data = {'email_body': email_body, 'to_email': emails,
                          'email_subject': "You've been invited to Livestock Manager"}
            users = []
            for email in emails:
                user = User(email=email, role='USER', is_active=True,
                            company=company)
                user.set_password(email)
                user.save()
                serializer = UserSerializer(instance=user, context={
                    'request': request})
                users.append(serializer.data)

            Util.send_email(email_data)
            return Response(users)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def list(self, request, authentication_classes=[TokenAuthentication]):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            users = User.objects.filter(company=company, deleted=False)
            serializer = self.get_serializer(users, many=True)
            page = self.paginate_queryset(serializer.data['users'])
            if page is not None:
                return self.get_paginated_response(page)
            else:
                return Response(serializer.data['users'])
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def partial_update(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        try:
            user = Util.authenticate(request, False)
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
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer

    @action(detail=False, methods=['get'])
    def get_upcoming_births(self, request):
        try:
            companies = Company.objects.all()
            serializer = self.get_serializer(companies, many=True)
            results = []
            for company in serializer.data:
                tasks = company.get('tasks')
                if tasks is not None:
                    def is_next_week(x):
                        d = datetime.datetime.strptime(x, "%Y-%m-%d")
                        now = datetime.datetime.now()
                        return (d - now).days < 7

                    def breeding(t):
                        is_breeding = t.get('due_date')
                        if is_breeding is None:
                            return False
                        elif is_next_week(is_breeding):
                            return True
                        else:
                            return False

                    filtered = filter(breeding, tasks)
                    has_results = len(list(filtered)) > 0
                    if has_results:
                        results.append({
                            "email": company['email'],
                            "tasks": filtered
                        })
            return Response(results)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['get'], authentication_classes=[TokenAuthentication])
    def get_stripe_account(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            if user['role'] == 'ADMIN':
                data = Stripe.retrieve_account(pk)
                return Response(data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['post'], authentication_classes=[TokenAuthentication])
    def update_stripe_account(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            if user['role'] == 'ADMIN':
                data = Stripe.update_account(request, pk)
                return Response(data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def partial_update(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        try:
            user = Util.authenticate(request, False)
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
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    # permission_classes = [IsAuthenticated]


class BreedingSetViewSet(viewsets.ModelViewSet):
    queryset = BreedingSet.objects.all()
    serializer_class = BreedingSetSerializer


class TransferViewSet(viewsets.ModelViewSet):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer

    @action(detail=False, methods=['post'])
    def check_for_transfer(self, request, pk=None):
        email = request.data['email']
        try:
            transfer = Transfer.objects.filter(
                email=email, accepted=False, transferred=False).first()
        except Transfer.DoesNotExist:
            transfer = None
        if transfer is not None:
            serializer = self.get_serializer(transfer)
            return Response(serializer.data)
        else:
            return Response(transfer)

    @action(detail=True, methods=['post'])
    def retrieve_transfer(self, request, pk=None):
        try:
            transfer = Transfer.objects.get(id=pk)
            if transfer.accepted or transfer.transferred:
                return Response(None)
            else:
                serializer = self.get_serializer(transfer)
                return Response(serializer.data)
        except Transfer.DoesNotExist:
            return Response(None)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'])
    def accept(self, request, pk=None):
        try:
            transfer_id = request.data['id']
            transfer = Transfer.objects.get(id=transfer_id)
            transfer.accepted = True
            try:
                company = Company.objects.get(email=transfer.email)
            except Company.DoesNotExist:
                company = None
            if company is not None:
                items = InvoiceItem.objects.filter(sale=transfer.sale)
                for item in items:
                    animal = item.animal
                    inventory = item.inventory
                    if animal is not None:
                        animal.company = company
                        animal.save()
                    if inventory is not None:
                        u = inventory.units
                        q = item.quantity
                        is_all = u - q <= 0
                        if is_all:
                            inventory.company = company
                            inventory.save()
                        else:
                            copy = Inventory.objects.get(id=inventory.id)
                            copy.id = None
                            copy.company = company
                            copy.units = item.quantity
                            inventory.units = inventory.units - item.quantity
                            copy.save()
                            inventory.save()
                transfer.transferred = True
            transfer.save()
            email_body = 'Your invoice sent to ' + \
                transfer.email+' has been accepted.'
            email_data = {
                'email_body': email_body,
                'to_email': [transfer.email],
                'email_subject': 'Your invoice has been accepted'
            }
            Util.send_email(email_data)
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'])
    def deny(self, request, pk=None):
        try:
            transfer_id = request.data['id']
            transfer = Transfer.objects.get(id=transfer_id)
            email_body = 'Your invoice sent to ' + \
                transfer.email+' has been denied and removed.'
            email_data = {
                'email_body': email_body,
                'to_email': [transfer.email],
                'email_subject': 'Your invoice has been denied'
            }
            Util.send_email(email_data)
            transfer.sale.delete()
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'], authentication_classes=[TokenAuthentication])
    def get_pdf(self, request):
        try:
            table_data = Util.get_pdf_data(request, 'animal')
            pdf = Util.export_pdf(request, 'animals.csv', table_data)
            return pdf
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def upload_csv(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            animals = []
            fieldnames = ['Name', 'Type',
                          'Sub-type', 'Tag Number', 'Registration Number', 'DOB', 'Father ID', 'Mother ID', 'Father Name', 'Mother Name']
            csv_file = request.data['csv']
            rows = Util.csv_data(csv_file, fieldnames)
            for row in rows:
                o = loads(dumps(row))
                father_placeholder = o.get('Father Name')
                mother_placeholder = o.get('Mother Name')
                f_id = o.get('Father ID')
                m_id = o.get('Mother ID')
                try:
                    father = Animal.objects.get(id=f_id)
                except Animal.DoesNotExist:
                    father = None
                try:
                    mother = Animal.objects.get(id=m_id)
                except Animal.DoesNotExist:
                    mother = None

                animal = Animal(
                    company=company,
                    name=o['Name'],
                    type=o['Type'],
                    sub_type=o['Sub-type'],
                    tag_number=o['Tag Number'],
                    registration_number=o['Registration Number'],
                    dob=o['DOB'],
                    father=father,
                    mother=mother,
                    father_placeholder=father_placeholder,
                    mother_placeholder=mother_placeholder,
                )
                animals.append(animal)
                print('ANIMALS', animals)
            results = Animal.objects.bulk_create(animals)
            serializer = self.get_serializer(results, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def delete_attachment(self, request):
        try:
            url = request.data['url']
            animal_id = request.data['id']
            Util.delete_file(url)
            animal = Animal.objects.get(id=animal_id)
            animal.attachment = None
            animal.save()
            serializer = self.get_serializer(animal)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def search(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            value = request.data['value']
            animals = Animal.objects.filter(
                Q(name__icontains=value, company=company, deleted=False) | Q(
                    tag_number__icontains=value, company=company, deleted=False)
            )
            page = self.paginate_queryset(animals)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(animals, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['post'], authentication_classes=[TokenAuthentication])
    def bred_info(self, request, pk=None):
        try:
            animal = Animal.objects.get(id=pk)
            breed_set = BreedingSet.objects.filter(
                Q(female=animal) | Q(animal_semen=animal)).first()
            if breed_set is not None:
                serializer = BreedingSetSerializer(instance=breed_set, context={
                    'request': request})
                breed_id = serializer.data['id']
                task = Task.objects.filter(
                    breeding_sets__id=breed_id).first()
                task_serializer = TaskSerializer(instance=task, context={
                    'request': request})
                response = {
                    'set': serializer.data,
                    'due_date': task_serializer.data['due_date'],
                    'task_due_date': task_serializer.data['task_due_date']
                }
                return Response(response)
            else:
                return Response([])
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['get'], authentication_classes=[TokenAuthentication])
    def by_type(self, request, pk=None):
        try:
            animals = Animal.objects.filter(type=pk, deleted=False)
            page = self.paginate_queryset(animals)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(animals, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['post'], authentication_classes=[TokenAuthentication])
    def get_tasks(self, request, pk=None):
        try:
            animal = Animal.objects.get(id=pk)
            tasks = animal.task_set.all()
            serializer = TaskSerializer(instance=tasks, context={
                'request': request}, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def get_parents(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            a_type = request.data['type']
            males = ['BULL', 'STEER', 'WETHER', 'RAM',
                     'STUD', 'GELDING', 'BOAR', 'BARROW', 'BUCK']
            sires = []
            dams = []
            if type == 'N/A':
                animals = Animal.objects.filter(
                    company=company_id, deleted=False)
                serializer = self.get_serializer(animals, many=True)
                for animal in serializer.data:
                    if animal['sub_type'] in males:
                        sires.append(animal)
                    else:
                        dams.append(animal)
                return Response({"father": sires, "mother": dams})
            else:
                animals = Animal.objects.filter(
                    company=company_id, type=a_type, deleted=False)
                serializer = self.get_serializer(animals, many=True)
                for animal in serializer.data:
                    if animal['sub_type'] in males:
                        sires.append(animal)
                    else:
                        dams.append(animal)
                return Response({"father": sires, "mother": dams})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def get_offspring(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            sub_type = request.data['sub_type']
            animal_id = request.data['id']
            animal = Animal.objects.get(id=animal_id)
            males = ['BULL', 'STEER', 'WETHER', 'RAM',
                     'STUD', 'GELDING', 'BOAR', 'BARROW', 'BUCK']
            if sub_type in males:
                children = Animal.objects.filter(
                    company=company_id, father=animal)
                serializer = self.get_serializer(children, many=True)
                return Response(serializer.data)
            else:
                children = Animal.objects.filter(
                    company=company_id, mother=animal)
                serializer = self.get_serializer(children, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def batch_delete(self, request, pk=None):
        try:
            animals = request.data['animals']
            for animal in Animal.objects.filter(id__in=animals):
                animal.deleted = True
                animal.save()
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def list(self, request, authentication_classes=[TokenAuthentication]):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            animals = Animal.objects.filter(company=company_id, deleted=False)
            page = self.paginate_queryset(animals)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(animals, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def create(self, request, authentication_classes=[TokenAuthentication]):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            data = request.data
            header_image = Util.upload_file(data['header_image'])
            breed = data.get('breed')
            profile_image = Util.upload_file(data['profile_image'])
            attachment_file = data.get("attachment")
            attachment = None if attachment_file == None else Util.upload_file(
                attachment_file)
            father = None if data.get(
                'father') == None else Animal.objects.get(id=data['father'])
            mother = None if data.get(
                'mother') == None else Animal.objects.get(id=data['mother'])
            father_placeholder = data.get('father_placeholder')
            mother_placeholder = data.get('mother_placeholder')

            new_animal = Animal.objects.create(
                name=data['name'],
                type=data['type'],
                sub_type=data['sub_type'],
                breed=breed,
                header_image=header_image,
                profile_image=profile_image,
                tag_number=data['tag_number'],
                registration_number=data['registration_number'],
                dob=data['dob'],
                father=father,
                mother=mother,
                attachment=attachment,
                company=company,
                father_placeholder=father_placeholder,
                mother_placeholder=mother_placeholder
            )
            serializer = self.get_serializer(new_animal)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def retrieve(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        try:
            animal = Animal.objects.get(id=pk)
            serializer = self.get_serializer(animal)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def partial_update(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        try:
            data = request.data
            sub_type = data['sub_type']
            tag_number = data['tag_number']
            registration_number = data['registration_number']
            breed = data.get('breed')
            name = data['name']
            attachment_file = data.get('attachment')
            header_img = data.get('header_image')
            profile_img = data.get('profile_image')
            if profile_img is None:
                profile_image = None
            elif type(profile_img) is str:
                profile_image = profile_img
            else:
                profile_image = Util.upload_file(profile_img)

            if header_img is None:
                header_image = None
            elif type(header_img) is str:
                header_image = header_img
            else:
                header_image = Util.upload_file(header_img)

            attachment = None if attachment_file == None else Util.upload_file(
                attachment_file)

            Animal.objects.filter(id=pk).update(
                sub_type=sub_type,
                tag_number=tag_number,
                registration_number=registration_number,
                breed=breed,
                name=name,
                attachment=attachment,
                profile_image=profile_image,
                header_image=header_image
            )
            updated = Animal.objects.get(id=pk)
            serializer = self.get_serializer(updated)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'], authentication_classes=[TokenAuthentication])
    def get_pdf(self, request):
        try:
            table_data = Util.get_pdf_data(request, 'inventory')
            pdf = Util.export_pdf(request, 'inventory.csv', table_data)
            return pdf
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def upload_csv(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            inventory = []
            fieldnames = ['Category', 'Cost',
                          'Tank Number', 'Canister Number', 'Top ID', 'Father ID', 'Mother ID', 'Units', 'Animal Category']
            csv_file = request.data['csv']
            rows = Util.csv_data(csv_file, fieldnames)
            for row in rows:
                o = loads(dumps(row))
                print(o)
                f_id = o.get('Father ID')
                m_id = o.get('Mother ID')
                try:
                    father = Animal.objects.get(id=f_id)
                except Animal.DoesNotExist:
                    father = None
                try:
                    mother = Animal.objects.get(id=m_id)
                except Animal.DoesNotExist:
                    mother = None
                item = Inventory(
                    company=company,
                    category=o['Category'],
                    cost=o['Cost'],
                    tank_number=o['Tank Number'],
                    canister_number=o['Canister Number'],
                    top_id=o['Top ID'],
                    father=father,
                    mother=mother,
                    units=o['Units'],
                    animal_category=o['Animal Category']
                )
                inventory.append(item)
            results = Inventory.objects.bulk_create(inventory)
            print('RESULTS', results)
            serializer = self.get_serializer(results, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def search(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            value = request.data['value']
            inventory = Inventory.objects.filter(
                Q(top_id__icontains=value, company=company, deleted=False) | Q(
                    tank_number__icontains=value, company=company, deleted=False)
            )
            page = self.paginate_queryset(inventory)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(inventory, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['get'], authentication_classes=[TokenAuthentication])
    def by_type(self, request, pk=None):
        try:
            inventory = Inventory.objects.filter(category=pk, deleted=False)
            serializer = self.get_serializer(inventory, many=True)
            page = self.paginate_queryset(inventory)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(inventory, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def get_breeding_sets(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            animal_category = request.data['type']
            inventory = Inventory.objects.filter(
                company=company, animal_category=animal_category, category='SEMEN', deleted=False
            )
            animals = Animal.objects.filter(
                company=company, type=animal_category, deleted=False)
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
            response = {
                "females": females,
                "semen": [*inventory_serializer.data, *males]
            }
            return Response(response)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def batch_delete(self, request, pk=None):
        try:
            inventory = request.data['inventory']
            for inv in Inventory.objects.filter(id__in=inventory):
                inv.deleted = True
                inv.save()
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def list(self, request, authentication_classes=[TokenAuthentication]):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            inventory = Inventory.objects.filter(
                company=company, deleted=False)
            page = self.paginate_queryset(inventory)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(inventory, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def create(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            data = request.data
            category = data['category']
            cost = data['cost']
            tank_number = data['tank_number']
            canister_number = data['canister_number']
            top_id = data['top_id']
            father_id = data.get('father')
            father = None if father_id == None or father_id == 'N/A' else Animal.objects.get(
                id=father_id)
            mother_id = data.get('mother')
            mother = None if mother_id == None or mother_id == 'N/A' else Animal.objects.get(
                id=mother_id)
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
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def partial_update(self, request, pk=None, authentication_classes=[TokenAuthentication]):
        try:
            data = request.data
            cost = data['cost']
            tank_number = data['tank_number']
            canister_number = data['canister_number']
            top_id = data['top_id']
            units = data['units']
            Inventory.objects.filter(id=pk).update(
                cost=cost,
                tank_number=tank_number,
                canister_number=canister_number,
                top_id=top_id,
                units=units
            )
            inventory = Inventory.objects.get(id=pk)
            serializer = self.get_serializer(inventory)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)


class InvoiceItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=True, methods=['get'])
    def get_sales_for_animal(self, request, pk=None):
        try:
            parent = Animal.objects.get(id=pk)
            children_ids = Animal.objects.filter(Q(father=parent) | Q(
                mother=parent)).values_list('pk', flat=True)
            inventory_ids = Inventory.objects.filter(Q(father=parent) | Q(
                mother=parent)).values_list('pk', flat=True)
            livestock_items = InvoiceItem.objects.filter(
                animal__in=list(children_ids))
            inventory_items = InvoiceItem.objects.filter(
                inventory__in=list(inventory_ids))
            livestock_serializer = self.get_serializer(
                livestock_items, many=True)
            inventory_serializer = self.get_serializer(
                inventory_items, many=True)

            def paid(item):
                if item['sale']['status'] == 'PAID':
                    return item

            offspring = filter(paid, livestock_serializer.data)
            inventory = filter(paid, inventory_serializer.data)
            bar_data = [livestock_serializer.data, inventory_serializer.data]

            sales = {
                "offspring": offspring,
                "inventory": inventory,
                "bar_data": bar_data
            }

            return Response(sales)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'])
    def get_pdf(self, request):
        try:
            table_data = Util.get_pdf_data(request, 'sale')
            pdf = Util.export_pdf(request, 'sales.csv', table_data)
            return pdf
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['get'])
    def by_type(self, request, pk=None):
        try:
            sales = Sale.objects.filter(status=pk, deleted=False)
            page = self.paginate_queryset(sales)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(sales, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['get'])
    def download_invoice(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            cs = CompanySerializer(instance=company, context={
                'request': request})
            sale = Sale.objects.get(id=pk)
            ss = self.get_serializer(sale)
            params = {'invoice': ss.data,
                      'company': cs.data}
            pdf = Util.create_invoice_file(params, True)
            return pdf
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'])
    def change_to_paid(self, request):
        try:
            invoices = request.data['invoices']
            Sale.objects.filter(id__in=invoices).update(status='PAID')
            return Response({'status': 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'])
    def resend_invoices(self, request):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            cs = CompanySerializer(instance=company, context={
                'request': request})
            for invoice in request.data['invoices']:
                email = invoice['email']
                sale_id = invoice['id']
                sale = Sale.objects.get(id=sale_id)
                serializer = self.get_serializer(sale)
                params = {'invoice': serializer.data,
                          'company': cs.data}
                html = Util.create_invoice_file(params, False)
                email_body = 'Your invoice is below.'
                email_data = {'email_body': email_body, 'to_email': [email],
                              'email_subject': 'You have been sent an invoice via Livestock Manager', 'html': html}
                Util.send_email(email_data)
            return Response('Email Sent')
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'])
    def search(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            value = request.data['value']
            sales = Sale.objects.filter(
                Q(bill_to_name__icontains=value, company=company, deleted=False) | Q(
                    number__icontains=value, company=company, deleted=False)
            )
            page = self.paginate_queryset(sales)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(sales, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def batch_delete(self, request, pk=None):
        try:
            sales = request.data['sales']
            for sale in Sale.objects.filter(id__in=sales):
                sale.deleted = True
                sale.save()
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def list(self, request):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            sales = Sale.objects.filter(company=company, deleted=False)
            page = self.paginate_queryset(sales)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            else:
                serializer = self.get_serializer(sales, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def create(self, request):
        try:
            user = Util.authenticate(request, False)
            data = request.data
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            number = data['number']
            due_date = data['due_date']
            issue_date = data['issue_date']
            title = data['title']
            bill_to_name = data['bill_to_name']
            bill_to_address = data['bill_to_address']
            email = data['bill_to_email']
            phone = data['phone']
            status = 'UNPAID'
            total = data['total']
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
                total=total,
                company=company
            )
            sale.save()
            for item in invoice_items:
                cost = int(item['cost'])
                description = item['description']
                quantity = int(item['quantity'])
                if item['type'] == 'LIVESTOCK':
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
            transfer = Transfer(email=email, sale=sale,
                                created_by=company.email)
            transfer.save()
            serializer = self.get_serializer(sale)
            company_serializer = CompanySerializer(instance=company, context={
                'request': request})
            url = settings.REACT_DOMAIN+'transfer/'+str(transfer.id)
            params = {
                'invoice': serializer.data,
                'company': company_serializer.data
            }
            html = Util.create_invoice_file(params, False)
            email_body = 'You have been sent an invoice via Livestock Manager. Accept or deny the transfer of items here '+url
            email_data = {'email_body': email_body, 'to_email': [email],
                          'email_subject': email_body, 'html': html}
            Util.send_email(email_data)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)


class TaskViewset(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        try:
            outdated = Task.objects.get(id=pk)
            outdated.completed = not outdated.completed
            outdated.save()
            task = Task.objects.get(id=pk)
            if task.category == 'BREEDING':
                sets = task.breeding_sets.all()
                for s in sets:
                    semen = s.inventory_semen
                    if semen is not None:
                        inventory = Inventory.objects.get(id=semen.id)
                        inventory.units = inventory.units - 1
                        inventory.save()
            else:
                animals = task.animals.all()
                expense_per = round(task.cost / len(animals), 2)
                for a in animals:
                    Expense.objects.create(
                        cost=expense_per, animal=a, task_type=task.category)
            serializer = self.get_serializer(task)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def search(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            value = request.data['value']
            tasks = Task.objects.filter(
                title__icontains=value, company=company, deleted=False)
            serializer = self.get_serializer(tasks, many=True)
            return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=True, methods=['post'], authentication_classes=[TokenAuthentication])
    def delete_single(self, request, pk=None):
        try:
            task = Task.objects.get(id=pk)
            task.deleted = True
            task.save()
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    @action(detail=False, methods=['post'], authentication_classes=[TokenAuthentication])
    def batch_delete(self, request, pk=None):
        try:
            tasks = request.data['tasks']
            for task in Task.objects.filter(id__in=tasks):
                task.deleted = True
                task.save()
            return Response({"status": 200})
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def list(self, request):
        try:
            user = Util.authenticate(request, False)
            company_id = user['company']['id']
            company = Company.objects.get(id=company_id)
            role = user['role']
            if role == 'ADMIN':
                tasks = Task.objects.filter(company=company, deleted=False)
                serializer = self.get_serializer(tasks, many=True)
                return Response(serializer.data)
            else:
                u = User.objects.get(id=user['id'])
                tasks = u.task_set.all()
                serializer = self.get_serializer(tasks, many=True)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def create(self, request, pk=None):
        try:
            user = Util.authenticate(request, False)
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
                cost = data['cost']
                animals = Animal.objects.filter(id__in=data['animals'])
                task = Task(
                    title=title,
                    category=category,
                    task_due_date=task_due_date,
                    description=description,
                    company=company,
                    cost=cost,
                    completed=False
                )
                task.save()
                task.users.set(users)
                task.animals.set(animals)
                serializer = self.get_serializer(task)
                return Response(serializer.data)
        except Exception as e:
            print(e)
            return HttpResponseServerError(e)

    def partial_update(self, request, pk=None):
        try:
            data = request.data
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
                Task.objects.filter(id=pk).update(
                    title=title,
                    category=category,
                    task_due_date=task_due_date,
                    description=description,
                    due_date=due_date
                )
                task = Task.objects.get(id=pk)
                task.users.clear()
                task.breeding_sets.clear()
                task.save()
                task.users.set(users)
                task.breeding_sets.set(breeding_sets)
                serializer = self.get_serializer(task)
                return Response(serializer.data)
            else:
                cost = data['cost']
                animals = Animal.objects.filter(id__in=data['animals'])
                Task.objects.filter(id=pk).update(
                    title=title,
                    category=category,
                    task_due_date=task_due_date,
                    description=description,
                    cost=cost
                )
                task = Task.objects.get(id=pk)
                task.users.clear()
                task.animals.clear()
                task.save()
                task.users.set(users)
                task.animals.set(animals)
                serializer = self.get_serializer(task)
                return Response(serializer.data)

        except Exception as e:
            print(e)
            return HttpResponseServerError(e)
