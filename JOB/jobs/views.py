from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Q, Count
from django.core.mail import send_mail
from .models import Employer, Candidate, Resume, JobListing, Application
from .serializers import (
    EmployerSerializer, CandidateSerializer, ResumeSerializer,
    JobListingSerializer, ApplicationSerializer
)
from .serializers import UserAdminSerializer
from .permissions import IsEmployer, IsCandidate
from django.contrib.auth.models import User
from django.http import HttpResponse
import csv

from rest_framework.permissions import AllowAny


class EmployerRegisterView(generics.CreateAPIView):
    serializer_class = EmployerSerializer
    permission_classes = (AllowAny,)


class CandidateRegisterView(generics.CreateAPIView):
    serializer_class = CandidateSerializer
    permission_classes = (AllowAny,)


class JobListCreateView(generics.ListCreateAPIView):
    queryset = JobListing.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = JobListingSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        user = self.request.user
        try:
            employer = user.employer_profile
        except Employer.DoesNotExist:
            raise PermissionError('Only employer users can create jobs')
        serializer.save(employer=employer)


class JobSearchView(generics.ListAPIView):
    serializer_class = JobListingSerializer

    def get_queryset(self):
        qs = JobListing.objects.filter(is_active=True)
        q = self.request.query_params.get('q')
        location = self.request.query_params.get('location')
        min_salary = self.request.query_params.get('min_salary')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
        if location:
            qs = qs.filter(location__icontains=location)
        if min_salary:
            try:
                qs = qs.filter(salary__gte=float(min_salary))
            except ValueError:
                pass
        return qs.order_by('-created_at')


class ResumeUploadView(generics.CreateAPIView):
    serializer_class = ResumeSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        user = self.request.user
        try:
            candidate = user.candidate_profile
        except Candidate.DoesNotExist:
            raise PermissionError('Only candidate users can upload resumes')
        serializer.save(candidate=candidate)


class ApplicationCreateView(generics.CreateAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = (IsAuthenticated,)

    def perform_create(self, serializer):
        user = self.request.user
        try:
            candidate = user.candidate_profile
        except Candidate.DoesNotExist:
            raise PermissionError('Only candidate users can apply for jobs')
        serializer.save(candidate=candidate)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        # Notify employer (console/email)
        employer = application.job.employer
        subject = f"New application for {application.job.title}"
        message = f"Candidate {application.candidate} applied. Status: {application.status}"
        if employer.user.email:
            send_mail(subject, message, None, [employer.user.email])
        else:
            print(subject, message)
        headers = self.get_success_headers(serializer.data)
        return Response(ApplicationSerializer(application).data, status=status.HTTP_201_CREATED, headers=headers)


class ApplicationListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer

    def get_queryset(self):
        qs = Application.objects.all().select_related('job', 'candidate')
        job_id = self.request.query_params.get('job')
        candidate_id = self.request.query_params.get('candidate')
        status_q = self.request.query_params.get('status')
        if job_id:
            qs = qs.filter(job_id=job_id)
        if candidate_id:
            qs = qs.filter(candidate_id=candidate_id)
        if status_q:
            qs = qs.filter(status=status_q)
        return qs.order_by('-applied_at')


@api_view(['POST'])
def update_application_status(request, pk):
    try:
        app = Application.objects.get(pk=pk)
    except Application.DoesNotExist:
        return Response({'detail':'Not found'}, status=status.HTTP_404_NOT_FOUND)
    status_val = request.data.get('status')
    if status_val not in dict(Application.STATUS_CHOICES):
        return Response({'detail':'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
    app.status = status_val
    app.save()
    # audit log
    try:
        from .models import AuditLog
        AuditLog.objects.create(
            user=request.user if request.user.is_authenticated else None,
            action='update_application_status',
            object_type='Application',
            object_id=str(app.id),
            changes=f'status={status_val}'
        )
    except Exception:
        pass
    # notify candidate
    candidate_email = app.candidate.user.email
    subj = f"Your application status updated: {app.job.title}"
    msg = f"Status: {app.status}"
    if candidate_email:
        send_mail(subj, msg, None, [candidate_email])
    else:
        print(subj, msg)
    return Response(ApplicationSerializer(app).data)


@api_view(['GET'])
def reporting_stats(request):
    total_jobs = JobListing.objects.count()
    total_applications = Application.objects.count()
    by_status = dict(Application.objects.values('status').annotate(count=Count('id')).values_list('status', 'count'))
    # simple stats
    data = {
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'by_status': by_status,
    }
    return Response(data)


class EmployerReportView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        # pk = employer id
        try:
            employer = Employer.objects.get(pk=pk)
        except Employer.DoesNotExist:
            return Response({'detail': 'Employer not found'}, status=404)
        jobs = employer.jobs.all()
        jobs_stats = []
        for job in jobs:
            total = job.applications.count()
            by_status = dict(job.applications.values('status').annotate(count=Count('id')).values_list('status', 'count'))
            jobs_stats.append({'job_id': job.id, 'title': job.title, 'total_applications': total, 'by_status': by_status})
        data = {'employer_id': employer.id, 'company_name': employer.company_name, 'jobs': jobs_stats}
        # CSV export
        if request.query_params.get('format') == 'csv':
            resp = HttpResponse(content_type='text/csv')
            resp['Content-Disposition'] = f'attachment; filename=employer_{employer.id}_report.csv'
            writer = csv.writer(resp)
            writer.writerow(['job_id', 'title', 'total_applications', 'by_status'])
            for j in jobs_stats:
                writer.writerow([j['job_id'], j['title'], j['total_applications'], str(j['by_status'])])
            return resp
        return Response(data)


class JobReportView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        try:
            job = JobListing.objects.get(pk=pk)
        except JobListing.DoesNotExist:
            return Response({'detail': 'Job not found'}, status=404)
        total = job.applications.count()
        by_status = dict(job.applications.values('status').annotate(count=Count('id')).values_list('status', 'count'))
        data = {'job_id': job.id, 'title': job.title, 'total_applications': total, 'by_status': by_status}
        if request.query_params.get('format') == 'csv':
            resp = HttpResponse(content_type='text/csv')
            resp['Content-Disposition'] = f'attachment; filename=job_{job.id}_report.csv'
            writer = csv.writer(resp)
            writer.writerow(['job_id', 'title', 'total_applications', 'by_status'])
            writer.writerow([job.id, job.title, total, str(by_status)])
            return resp
        return Response(data)


class UserListAdminView(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserAdminSerializer

    def get_queryset(self):
        if not self.request.user.is_staff:
            return User.objects.none()
        return User.objects.all().order_by('-id')


class UserDetailAdminView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserAdminSerializer
    queryset = User.objects.all()

    def perform_update(self, serializer):
        user = serializer.save()
        # audit
        try:
            from .models import AuditLog
            AuditLog.objects.create(
                user=self.request.user if self.request.user.is_authenticated else None,
                action='admin_update_user',
                object_type='User',
                object_id=str(user.id),
                changes=str(serializer.validated_data)
            )
        except Exception:
            pass
