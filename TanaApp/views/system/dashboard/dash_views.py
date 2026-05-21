from django.shortcuts import render, redirect
from rest_framework.views import APIView
from django.views import View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from TanaApp.models import DbContract, DbOwner, DbBuilding, DbWarranty, DBPartialPyment
from django.utils import timezone
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, render
from rest_framework.request import Request
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from django.contrib.auth.mixins import LoginRequiredMixin

from TanaApp.views.owners.serializers import OwnerSerializer
from TanaApp.views.buildings.serializers import BuildingSerializer

class IndexView(LoginRequiredMixin, APIView):
    def get(self, request):
        return redirect('dashboard')

class DashboardView(LoginRequiredMixin, APIView):
    def get(self, request):
        # DbWarranty.objects.filter(end_date__lt=timezone.now())
        today = timezone.now()
        active_contract_building_ids = DbContract.objects.filter(
            end_date__gte=today
        ).values_list("building_id", flat=True)

        active_contract_elevator_ids = DbContract.objects.filter(
            end_date__gte=today
        ).values_list("elevators__id", flat=True)
        expired_warranties = DbWarranty.objects.filter(
            end_date__lt=today
        ).exclude(
            elevator__building_id__in=active_contract_building_ids
        ).exclude(
            elevator_id__in=active_contract_elevator_ids
        )
        data = {
            'owners': DbOwner.objects.all(),
            'buildings': DbBuilding.objects.all(),
            'active_contracts': DbContract.objects.filter(payed__in=[2, 3]),
            'warranties': expired_warranties,
            'pending_payments': DBPartialPyment.objects.all()
        }

        return render(request, 'pages/webs/dashboard.html', context={'data': data})

class OwnerListView(LoginRequiredMixin, ListView):
    model = DbOwner
    template_name = 'pages/webs/owner_list.html'
    context_object_name = 'owners'
    # paginate_by = 10  # optional: add pagination

class OwnerDetailView(LoginRequiredMixin, DetailView):
    model = DbOwner
    template_name = 'pages/webs/owner_detail.html'
    context_object_name = 'owner'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        owner = self.get_object()

        # Multiple context-based approach
        context['building_list'] = DbBuilding.objects.filter(owner=owner)
        return context

class OwnerCreateView(LoginRequiredMixin, View):
    # model = DbOwner
    # fields = ['name', 'phone_number', 'address']  # Adjust as needed
    # template_name = 'pages/webs/owner_create.html'

    def get(self, request):
        serializer = OwnerSerializer()
        return render(request, 'pages/webs/owner_create.html', {'serializer': serializer})

    def post(self, request):
        drf_request = Request(request, parsers=[FormParser(), MultiPartParser()])
        serializer = OwnerSerializer(data=drf_request.data)
        if serializer.is_valid():
            serializer.save()
            return redirect('owner-list')
        return render(request, 'pages/webs/owner_create.html', {'serializer': serializer})


class AddBuildingForOwnerAPIView(LoginRequiredMixin, APIView):
    def get(self, request, pk):
        owner = get_object_or_404(DbOwner, pk=pk)
        return render(request, 'pages/webs/owners/add_building_for_owner.html', {'owner': owner})

    def post(self, request, pk):
        owner = get_object_or_404(DbOwner, pk=pk)
        data = request.data.copy()
        data['owner'] = owner.id
        serializer = BuildingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Building created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
