from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from TanaApp.models import GlobalSettings, PersonalizedSettings
from .serializers import GlobalSettingsSerializer, PersonalizedSettingsSerializer


@method_decorator(login_required, name='dispatch')
class SettingsView(View):
    template_name = 'pages/webs/settings/settings.html'

    def get(self, request):
        global_data = {}
        if request.user.is_superuser:
            global_settings = GlobalSettings.objects.first()
            global_data = GlobalSettingsSerializer(global_settings).data if global_settings else {}

        personalized_settings, _ = PersonalizedSettings.objects.get_or_create(user=request.user)
        personal_data = PersonalizedSettingsSerializer(personalized_settings).data

        return render(request, self.template_name, {
            'global_settings': global_data,
            'personal_settings': personal_data,
            'is_superuser': request.user.is_superuser
        })


class SettingsAPIView(APIView):
    def post(self, request):
        user = request.user
        response_data = {}
        status_code = status.HTTP_200_OK

        # Handle global settings update
        if user.is_superuser and 'global_settings' in request.data:
            global_settings = GlobalSettings.objects.first()
            if not global_settings:
                global_settings = GlobalSettings()

            serializer = GlobalSettingsSerializer(
                global_settings,
                data=request.data['global_settings'],
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                response_data['global'] = serializer.data
            else:
                response_data['global_errors'] = serializer.errors
                status_code = status.HTTP_400_BAD_REQUEST

        # Handle personal settings
        if 'personal_settings' in request.data:
            personalized_settings, _ = PersonalizedSettings.objects.get_or_create(user=user)
            serializer = PersonalizedSettingsSerializer(
                personalized_settings,
                data=request.data['personal_settings'],
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                response_data['personal'] = serializer.data
            else:
                response_data['personal_errors'] = serializer.errors
                status_code = status.HTTP_400_BAD_REQUEST

        return Response(response_data, status=status_code)