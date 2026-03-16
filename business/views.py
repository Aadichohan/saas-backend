# from django.shortcuts import render


from rest_framework.viewsets import ModelViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from datetime import datetime
from business.models import Business
from business.BusinessSerializer import BusinessSerializer
from django_inventory_management.response import DrfResponse
from role_permission.role_based_permission import RoleBasedPermission


class BusinessViewSet(ModelViewSet):
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [RoleBasedPermission, IsAuthenticated]
    
    def list(self, request):
        business = Business.objects.all()
        business_serializer = BusinessSerializer(business, many=True)
        print(business_serializer)
        return DrfResponse(
            data    = business_serializer.data, 
            status  = status.HTTP_200_OK, 
            error   = {}, 
            headers = {}
        ).to_json()

    def create(self, request):
        business_serializer = self.get_serializer(data=request.data)
        if business_serializer.is_valid():
            user = self.request.user
            business_serializer.save(created_by=user)
            return DrfResponse( 
                data    = [business_serializer.data], 
                status  = status.HTTP_201_CREATED, 
                error   = {}, 
                response = {'response': 'business created successfully'},
                headers = {}
            ).to_json()
        # print(business_serializer.errors)
        return DrfResponse( 
            data    = [business_serializer.data], 
            status  = status.HTTP_400_BAD_REQUEST, 
            error   = [business_serializer.errors], 
            response = {'response': 'Something went wrong'},
            headers = {}
        ).to_json()
        

    def retrieve(self, request, pk=None):
        business = self.get_object()
        business_serializer = self.get_serializer(business)
        return DrfResponse(
            data    = [business_serializer.data], 
            status  = status.HTTP_200_OK, 
            error   = {}, 
            headers = {}
        ).to_json()

    def update(self, request, pk=None):
        business = self.get_object()
        business_serializer = self.get_serializer(business, data= request.data)
        user = self.request.user
        if business_serializer.is_valid():
            business_serializer.save(updated_by= user, updated_at=datetime.utcnow())

            return DrfResponse( 
                data    = [business_serializer.data], 
                status  = status.HTTP_200_OK, 
                error   = {}, 
                response = {'response': 'business updated successfully'},
                headers = {}
            ).to_json()
        
        return DrfResponse( 
            data    = [business_serializer.data], 
            status  = status.HTTP_400_BAD_REQUEST, 
            error   = [business_serializer.errors], 
            response = {'response': 'Something went wrong'},
            headers = {}
        ).to_json()

    def partial_update(self, request, pk=None):
        business = self.get_object()
        business_serializer = self.get_serializer(business, data= request.data, partial=True)
        if business_serializer.is_valid():
            business_serializer.save()

            return DrfResponse( 
                data    = [business_serializer.data], 
                status  = status.HTTP_200_OK, 
                error   = {}, 
                response = {'response': 'business updated successfully'},
                headers = {}
            ).to_json()
        
        return DrfResponse( 
            data    = [business_serializer.data], 
            status  = status.HTTP_400_BAD_REQUEST, 
            error   = [business_serializer.errors], 
            response = {'response': 'Something went wrong'},
            headers = {}
        ).to_json()

    def destroy(self, request, pk=None):
        business = self.get_object()
        user = self.request.user
        # business.delete()
        data = {
            "is_active": 0,
            "updated_by": user.pk,
            "updated_at": datetime.utcnow()
        }
        business_serializer = self.get_serializer(business, data= data, partial=True)
        if business_serializer.is_valid():
            business_serializer.save()
            # business_serializer.save(updated_by= user, updated_at=datetime.utcnow(), is_active = 0)
        return DrfResponse( 
         
            status  = status.HTTP_204_NO_CONTENT, 
            error   = {}, 
            response = {'response': 'business deleted successfully'},
            headers = {}
        ).to_json()
    
    # Custom action for marking a business as favorite (example)
    # @action(detail=True, methods=['post'])
    # def favorite(self, request, pk=None):
    #     business = self.get_object()
    #     business.desc = 'favorite'
    #     business.save()
    #     return Response({'status': 'business marked as favorite'})
