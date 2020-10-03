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

from .models import (
    User,
    Company,
    Address,
    Animal,
    Inventory,
    Task,
    InvoiceItem,
    Sale
)
from .serializers import (
    UserSerializer,
    CompanySerializer,
    AddressSerializer,
    AnimalSerializer,
    InventorySerializer,
    InvoiceItemSerializer,
    SaleSerializer,
)


class VerifyEmail(APIView):
    def get(self):
        pass


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [IsAuthenticated]
    # authentication_classes = [TokenAuthentication]

    @action(detail=True, methods=['post'])
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
            company=company
        )
        user.set_password(password)
        user.save()
        serializer = UserSerializer(instance=user, context={
            'request': request})

        token = 'Token.objects.create(user=user)'
        print('token', token)
        current_site = get_current_site(request).domain
        link = reverse('verify-email')
        absurl = 'http://'+current_site+link+"token=?"+token
        email_body = 'Hi '+user.first_name+' '+user.last_name + \
            ' Use the link below to verify your email \n' + absurl
        email_data = {'email_body': email_body, 'to_email': user.email,
                      'email_subject': 'Verify your email'}
        Util.send_email(email_data)

        return Response({
            'user': serializer.data,
            'token': token
        })

    def create(self, request):
        current_site = get_current_site(request).domain
        absurl = 'http://'+current_site+"/login"
        email_body = 'Hello,' \
            " You've been invited to use Livestock Manager. Please click the link to login using your email as your email and password. Password can be changed after in your profile \n" + absurl
        emails = request.data['emails']
        company = Company.objects.first()

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


class AnimalViewSet(viewsets.ModelViewSet):
    queryset = Animal.objects.all()
    serializer_class = AnimalSerializer
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'])
    def get_pdf(self, request):
        table_data = Util.get_pdf_data(request, 'animal')
        pdf = Util.export_pdf(request, 'animals.pdf', table_data)
        return pdf

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
        company = user['company']
        data = request.data
        header_image = Util.upload_file(data['header_image'])
        profile_image = Util.upload_file(data['profile_image'])
        attachment = Util.upload_file(data['attachment'])
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


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    # permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def get_pdf(self, request):
        table_data = Util.get_pdf_data(request, 'inventory')
        pdf = Util.export_pdf(request, 'inventory.pdf', table_data)
        return pdf


class InvoiceItemViewSet(viewsets.ModelViewSet):
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    # permission_classes = [IsAuthenticated]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    # permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def get_pdf(self, request):
        table_data = Util.get_pdf_data(request, 'sale')
        pdf = Util.export_pdf(request, 'sales.pdf', table_data)
        return pdf
