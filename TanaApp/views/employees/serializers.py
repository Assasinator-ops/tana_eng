from rest_framework import serializers
from TanaApp.models import DbUser, UserType

class EmployeeSerializer(serializers.ModelSerializer):
    usertype = serializers.ChoiceField(choices=UserType.choices)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = DbUser
        fields = ['id', 'name', 'email', 'usertype', 'phone', 'password', 'status']
        extra_kwargs = {
            'email': {'validators': []}  # Disable default unique validator
        }

class EmployeeUpdateSerializer(serializers.ModelSerializer):
    usertype = serializers.ChoiceField(choices=UserType.choices, required=False)

    class Meta:
        model = DbUser
        fields = ['name', 'email', 'usertype', 'phone', 'status']