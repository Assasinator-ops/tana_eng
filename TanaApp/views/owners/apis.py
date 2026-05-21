from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from django.db.models import Q
from TanaApp.models import DbOwner
from .serializers import OwnerSerializer

class OwnerListCreateView(generics.ListCreateAPIView):
    queryset = DbOwner.objects.all()
    serializer_class = OwnerSerializer
    permission_classes = [permissions.IsAuthenticated]
    template_name = 'rest_framework/api.html'  # Browsable API template

    def get_queryset(self):
        # Handle sorting parameters (e.g., ?sort=name&what=1)
        sort = self.request.query_params.get('sort', 'id')
        what = int(self.request.query_params.get('what', 1))
        order_by = f"{'' if what else '-'}{sort}"
        return super().get_queryset().order_by(order_by)

class OwnerRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = DbOwner.objects.all()
    serializer_class = OwnerSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_object(self, id):
        try:
            return DbOwner.objects.get(id=id)
        except DbOwner.DoesNotExist:
            raise NotFound(detail="Owner not found.")

    def get(self, request, id):
        owner = self.get_object(id)
        serializer = OwnerSerializer(owner)
        return Response(serializer.data)

    def post(self, request, id):
        owner = self.get_object(id)
        action = request.data.get('action')
        if action == 'delete':
            # delete logic
            if owner.building.exists():
                raise ValidationError(
                    {"detail": "Owner cannot be deleted because it has associated buildings."}
                )
            owner.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        elif action == 'update':
            # update logic
            serializer = OwnerSerializer(owner, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(
                {"detail": "Invalid action. Must be 'update' or 'delete'."},
                status=status.HTTP_400_BAD_REQUEST
            )

class OwnerUpdateView(generics.UpdateAPIView):
    """Handles PUT (update) only."""
    queryset = DbOwner.objects.all()
    serializer_class = OwnerSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class OwnerSearchView(generics.ListAPIView):
    serializer_class = OwnerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        name = self.request.query_params.get('name', '')
        return DbOwner.objects.filter(
            Q(name__icontains=name) |
            Q(name__istartswith=name) |
            Q(name__iendswith=name)
        )