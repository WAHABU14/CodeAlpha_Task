from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Employer, Candidate, Resume, JobListing, Application


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')


class EmployerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Employer
        fields = ('id', 'user', 'company_name', 'website', 'description')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        employer = Employer.objects.create(user=user, **validated_data)
        return employer

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for attr, val in user_data.items():
                setattr(instance.user, attr, val)
            instance.user.save()
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance


class CandidateSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Candidate
        fields = ('id', 'user', 'phone', 'location')

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = User.objects.create_user(**user_data)
        candidate = Candidate.objects.create(user=user, **validated_data)
        return candidate

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            for attr, val in user_data.items():
                setattr(instance.user, attr, val)
            instance.user.save()
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        return instance


class ResumeSerializer(serializers.ModelSerializer):
    candidate = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Resume
        fields = ('id', 'candidate', 'file', 'uploaded_at')

    def validate_file(self, value):
        # limit to 5 MB
        max_mb = 5
        if value.size > max_mb * 1024 * 1024:
            raise serializers.ValidationError('File too large. Max size is 5 MB.')
        # basic content-type check by name
        name = value.name.lower()
        allowed = ('.pdf', '.doc', '.docx', '.txt')
        if not name.endswith(allowed):
            raise serializers.ValidationError('Unsupported file type.')
        return value


class JobListingSerializer(serializers.ModelSerializer):
    employer = EmployerSerializer(read_only=True)
    employer_id = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Employer.objects.all(), source='employer')

    class Meta:
        model = JobListing
        fields = ('id', 'employer', 'employer_id', 'title', 'description', 'location', 'salary', 'is_active', 'created_at')


class ApplicationSerializer(serializers.ModelSerializer):
    candidate = CandidateSerializer(read_only=True)
    candidate_id = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Candidate.objects.all(), source='candidate')
    resume_id = serializers.PrimaryKeyRelatedField(write_only=True, queryset=Resume.objects.all(), source='resume', allow_null=True, required=False)

    class Meta:
        model = Application
        fields = ('id', 'job', 'candidate', 'candidate_id', 'resume', 'resume_id', 'cover_letter', 'status', 'applied_at')
        read_only_fields = ('status', 'applied_at', 'resume')


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        from django.contrib.auth.models import User
        model = User
        fields = ('id', 'username', 'email', 'is_active', 'is_staff', 'is_superuser')
        read_only_fields = ('id',)
