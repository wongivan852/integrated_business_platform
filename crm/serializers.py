# serializers.py
from rest_framework import serializers
from .models import Customer, Course, Enrollment, Conference, ConferenceRegistration, CommunicationLog

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class CourseSerializer(serializers.ModelSerializer):
    enrolled_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_enrolled_count(self, obj):
        return obj.enrollment_set.filter(status__in=['registered', 'confirmed']).count()

class EnrollmentSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)
    
    class Meta:
        model = Enrollment
        fields = '__all__'
        read_only_fields = ('id', 'enrollment_date')

class ConferenceSerializer(serializers.ModelSerializer):
    registered_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Conference
        fields = '__all__'
        read_only_fields = ('id', 'created_at')
    
    def get_registered_count(self, obj):
        return obj.conferenceregistration_set.count()

class CommunicationLogSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.first_name', read_only=True)
    
    class Meta:
        model = CommunicationLog
        fields = '__all__'
        read_only_fields = ('id', 'sent_at')
