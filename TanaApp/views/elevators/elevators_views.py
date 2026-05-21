import datetime
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import status
from TanaApp.models import DbElevator, DbWarranty, DbContract, DbBuilding
from TanaApp.views.elevators.serializers import ElevatorSerializer
from TanaApp.views.contracts.serializers import ContractCreateSerializer
from TanaApp.contract_payment import get_payment_status_constraints
from django.utils.timezone import now, timedelta
from django.utils import timezone
from django.urls import reverse

class ElevatorDashboardView(LoginRequiredMixin, View):
    def get(self, request):
        elevators = DbElevator.objects.all()
        serializer = ElevatorSerializer(elevators, many=True)
        return render(request, 'pages/webs/elevators/dashboard.html', {'elevators': serializer.data})


class ElevatorAddView(LoginRequiredMixin, View):
    def get(self, request):
        serializer = ElevatorSerializer()
        return render(request, 'pages/webs/elevators/add.html', {'serializer': serializer})

    def post(self, request):
        data = request.POST.dict()
        serializer = ElevatorSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return redirect('elevator-dashboard')
        return render(request, 'pages/webs/elevators/add.html', {'error': serializer.errors})


class ElevatorDetailView(LoginRequiredMixin, View):
    def get(self, request, id):
        elevator = get_object_or_404(
            DbElevator.objects.select_related('building', 'building__owner'),
            id=id,
        )
        building = elevator.building
        # Get all visible warranties for the elevator
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
                contracts = warranty.elevator.contracts.all()
                if not contracts.exists():
                    visible_warranties.append(warranty)  # No contracts yet
                elif all(contract.end_date < now_time for contract in contracts):
                    visible_warranties.append(warranty)  # All contracts expired

        # Use this list as the valid warranties to show
        warranties = visible_warranties

        contracts = DbContract.objects.filter(
            building=elevator.building, end_date__gt=now()
        ).prefetch_related('elevators', 'extra', 'discount', 'partial')

        # Add computed fields for warranties
        now_date = now().date()
        now_time = timezone.now()
        today_start = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
        five_days_later = today_start + timedelta(days=5)
        for warranty in warranties:
            warranty.days_left = (warranty.end_date.date() - now_date).days
            warranty.duration = (warranty.end_date.date() - warranty.start_date.date()).days

        # Metrics
        contract_count = contracts.count()
        warranty_count = len(warranties)
        expired_contracts_count = contracts.filter(end_date__lt=today_start).count()
        expired_warranties_count = len([w for w in warranties if w.end_date < today_start])
        expiring_soon_count = contracts.filter(
            end_date__gte=today_start,
            end_date__lte=five_days_later
        ).count()
        create_next = request.GET.get('next', request.get_full_path())
        # contract_form = ContractCreateSerializer(building)
        contract_form = ContractCreateSerializer(context={'building': elevator.building.id})
        serializer = ElevatorSerializer(elevator)
        
        # Prepare contract data with attached elevators info
        enhanced_contracts = []
        for contract in contracts:
            attached_elevators = [elevator.id for elevator in contract.elevators.all()]
            is_current_elevator_attached = elevator in contract.elevators.all()
            payment_constraints = get_payment_status_constraints(contract)
            enhanced_contracts.append({
                'contract': contract,
                'attached_elevators': ', '.join(attached_elevators),
                'is_current_elevator_attached': is_current_elevator_attached,
                'payment_totals': payment_constraints,
                'can_mark_fully_paid': payment_constraints['can_mark_fully_paid'],
                'can_mark_not_paid': payment_constraints['can_mark_not_paid'],
                'can_mark_partial_paid': payment_constraints['can_mark_partial_paid'],
            })
        
        has_active_warranty = any(
            getattr(w, 'days_left', -1) > 0 for w in warranties
        )

        context = {
            'serializer': serializer,
            'elevator': elevator,
            'building': building,
            'has_active_warranty': has_active_warranty,
            'contracts': contracts,
            'enhanced_contracts': enhanced_contracts,
            'contract_form': contract_form,
            'contract_create_next': create_next,
            'warranties': warranties,
            'contract_count': contract_count,
            'warranty_count': warranty_count,
            'expired_contracts_count': expired_contracts_count,
            'expired_warranties_count': expired_warranties_count,
            'expiring_soon_count': expiring_soon_count,
        }
        return render(request, 'pages/webs/elevators/detail.html', context)

    def post(self, request, id):
        elevator = get_object_or_404(DbElevator, id=id)

        if "update" in request.POST:
            data = request.POST.dict()
            serializer = ElevatorSerializer(elevator, data=data)
            if serializer.is_valid():
                serializer.save()
                return redirect('elevator-dashboard')
            # error_serializer = ElevatorSerializer(elevator)
            return redirect('elevator-detail-page', id=id)  # Redirect back to detail page with errors in context

        elif "delete" in request.POST:
            elevator.delete()
            return redirect('elevator-dashboard')

        return redirect('elevator-detail', id=id)
    '''
        elevator = get_object_or_404(DbElevator, id=id)

        if "update" in request.POST:
            data = request.POST.dict()
            serializer = ElevatorSerializer(elevator, data=data)
            if serializer.is_valid():
                serializer.save()
                return redirect('elevator-dashboard')
            return render(request, 'pages/webs/elevators/detail.html', {'elevator': serializer.data, 'error': serializer.errors})

        elif "delete" in request.POST:
            elevator.delete()
            return redirect('elevator-dashboard')

        return redirect('elevator-detail', id=id)
    '''

class AddElevatorToContractView(LoginRequiredMixin, View):
    def get(self, request, contract_id):
        contract = get_object_or_404(DbContract, id=contract_id)
        building = contract.building

        # Elevators already in a contract (M2M field now)
        occupied_elevator_ids = DbContract.objects.values_list('elevators__id', flat=True)

        # Elevators whose warranty is expired
        expired_warranty_ids = DbWarranty.objects.filter(
            end_date__lt=now()
        ).values_list('elevator_id', flat=True)

        # Elevators available for assignment
        available_elevators = DbElevator.objects.filter(
            building=building
        ).exclude(
            id__in=occupied_elevator_ids
        ).filter(
            id__in=expired_warranty_ids
        )

        context = {
            'contract': contract,
            'elevators': available_elevators,
        }
        return render(request, 'pages/contracts/add_elevator.html', context)

    def post(self, request, contract_id):
        contract = get_object_or_404(DbContract, id=contract_id)
        elevator_ids = request.POST.getlist('elevator_ids')

        # Add elevators directly to the contract via ManyToManyField
        for eid in elevator_ids:
            elevator = get_object_or_404(DbElevator, id=eid)
            contract.elevators.add(elevator)

        return redirect(reverse('contracts-detail', args=[contract.id]))