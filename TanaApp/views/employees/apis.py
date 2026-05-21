from rest_framework import generics, permissions, status
from rest_framework.exceptions import NotFound, ValidationError
from TanaApp.models import DbUser
from .serializers import EmployeeSerializer, EmployeeUpdateSerializer

class EmployeeListCreateView(generics.ListCreateAPIView):
    queryset = DbUser.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    template_name = 'rest_framework/api.html'

    def handle_exception(self, exc):
        if isinstance(exc, ValidationError):
            return Response(
                {'detail': 'Employee already exists'},
                status=status.HTTP_409_CONFLICT
            )
        return super().handle_exception(exc)

class EmployeeRetrieveUpdateView(generics.RetrieveUpdateAPIView):
    queryset = DbUser.objects.all()
    serializer_class = EmployeeUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class EmployeeRetrieveByEmailView(generics.RetrieveAPIView):
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        email = self.request.query_params.get('email')
        try:
            employee = DbUser.objects.get(email=email)
            if not employee.status:
                raise ValidationError('Account disabled, contact admin')
            return employee
        except DbUser.DoesNotExist:
            raise NotFound('Employee not found')