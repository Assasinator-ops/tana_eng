from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import now
from django.db.models import Q

from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from TanaApp.models import DbBuilding, DbElevator, DbWarranty, DbContract
from TanaApp.views.buildings.serializers import BuildingSerializer
from TanaApp.views.elevators.serializers import ElevatorSerializer
from TanaApp.views.contracts.serializers import ContractCreateSerializer
from TanaApp.contract_payment import get_payment_status_constraints

class BuildingDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        buildings = DbBuilding.objects.all()
        serializer = BuildingSerializer(buildings, many=True)
        return render(request, 'pages/webs/buildings/dashboard.html', {'buildings': serializer.data})


class BuildingAddView(LoginRequiredMixin, View):
    def get(self, request):
        serializer = BuildingSerializer()
        return render(request, 'pages/webs/buildings/add.html', {'serializer': serializer})

    def post(self, request):
        data = request.POST.dict()
        serializer = BuildingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return redirect('buildings-dashboard')
        return render(request, 'pages/webs/buildings/add.html', {'error': serializer.errors})


class BuildingDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        building = get_object_or_404(DbBuilding, id=id)
        contracts = DbContract.objects.filter(building=building).prefetch_related(
            'elevators', 'extra', 'discount', 'partial'
        )
        contracts_with_payment = []
        for contract in contracts:
            payment_constraints = get_payment_status_constraints(contract)
            contracts_with_payment.append({
                'contract': contract,
                'payment_totals': payment_constraints,
                'can_mark_fully_paid': payment_constraints['can_mark_fully_paid'],
                'can_mark_not_paid': payment_constraints['can_mark_not_paid'],
                'can_mark_partial_paid': payment_constraints['can_mark_partial_paid'],
            })
        elevators = DbElevator.objects.filter(building=building).prefetch_related('contracts', 'warranty')

        # Prepare context for elevator statuses
        elevator_data = []
        current_time = now()

        for elevator in elevators:
            status = []
            # Get warranty
            warranty = DbWarranty.objects.filter(elevator=elevator).order_by('-end_date').first()
            if warranty:
                if warranty.end_date > current_time:
                    status.append("Under Warranty")
                else:
                    status.append("Warranty Expired")
            else:
                status.append("No Warranty")

            # Get contracts
            active_contract = elevator.contracts.filter(end_date__gt=current_time).first()
            expired_contract = elevator.contracts.filter(end_date__lt=current_time).first()

            if active_contract:
                status.append("Under Contract")
            elif expired_contract:
                status.append("Contract Expired")
            else:
                status.append("No Contract")

            # Add this elevator info
            elevator_data.append({
                'id': elevator.id,
                'name': elevator.name,
                'model': elevator.model,
                'number_of_stops': elevator.number_of_stops,
                'registered': elevator.registerd_date,
                'started': elevator.started_date,
                'total': elevator.Total,
                'status': status
            })

        warranties = DbWarranty.objects.filter(elevator=elevator)
        # Define now once for accuracy
        now_time = now()

        visible_warranties = []
        for warranty in warranties:
            if warranty.end_date >= now_time:
                # Warranty is still valid → show it
                visible_warranties.append(warranty)
            else:
                # Warranty expired → check contracts of elevator
                contractDatas = warranty.elevator.contracts.all()
                if not contractDatas.exists():
                    visible_warranties.append(warranty)  # No contracts yet
                elif all(contract.end_date < now_time for contract in contracts):
                    visible_warranties.append(warranty)  # All contracts expired

        # Use this list as the valid warranties to show
        warranties = visible_warranties

        serializer = BuildingSerializer(building)
        create_next = request.GET.get('next', request.get_full_path())
        contract_form = ContractCreateSerializer(context={'building': building.id})

        context = {
            'contracts': contracts,
            'contracts_with_payment': contracts_with_payment,
            'contract_form': contract_form,
            'contract_create_next': create_next,
            'building': serializer.data,
            'serializer': serializer,
            'elevators': elevator_data,
            'warranties': warranties,
        }
        return render(request, 'pages/webs/buildings/detail.html', context)

    def post(self, request, id):
        building = get_object_or_404(DbBuilding, id=id)

        if "update" in request.POST:
            data = request.POST.dict()
            serializer = BuildingSerializer(building, data=data)
            if serializer.is_valid():
                serializer.save()
                return redirect('buildings-dashboard')
            return render(request, 'pages/webs/buildings/detail.html', {'building': serializer.data, 'error': serializer.errors})

        elif "delete" in request.POST:
            building.delete()
            return redirect('buildings-dashboard')

        return redirect('buildings-detail-page', id=id)

class AddElevatorForBuildingAPIView(LoginRequiredMixin, APIView):
    def get(self, request, pk):
        building = get_object_or_404(DbBuilding, pk=pk)

        create_next = request.GET.get('next', request.get_full_path())
        contract_form = ContractCreateSerializer(context={'building': building.id})
        context = {
            'building': building,
            'contract_form': contract_form,
            'contract_create_next': create_next,
        }
        return render(request, 'pages/webs/buildings/add_elevator_for_building.html', context)

    def post(self, request, pk):
        building = get_object_or_404(DbBuilding, pk=pk)
        data = request.data.copy()
        data['building'] = building.id
        serializer = ElevatorSerializer(data=data)
        if serializer.is_valid():
            elevator = serializer.save()
            warranty_months = int(self.request.data.get('warranty_months', 12))
            DbWarranty.objects.create(
                elevator=elevator,
                start_date=timezone.now(),
                end_date=timezone.now() + relativedelta(months=+warranty_months)
            )
            return Response({'message': 'Elevator created successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)