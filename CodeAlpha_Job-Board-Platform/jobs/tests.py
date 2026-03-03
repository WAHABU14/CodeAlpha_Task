from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Employer, Candidate, JobListing, Resume, Application
from rest_framework.authtoken.models import Token


class JobsAPITestCase(TestCase):
    def setUp(self):
        # Users
        self.user_employer = User.objects.create_user(username='employer', email='employer@example.com', password='pass')
        self.user_candidate = User.objects.create_user(username='candidate', email='candidate@example.com', password='pass')
        # Profiles
        self.employer = Employer.objects.create(user=self.user_employer, company_name='Acme')
        self.candidate = Candidate.objects.create(user=self.user_candidate, phone='123', location='Remote')
        # Job
        self.job = JobListing.objects.create(employer=self.employer, title='Backend Engineer', description='Work on APIs', location='Remote', salary=80000)
        self.client = APIClient()
        # tokens
        self.token_candidate = Token.objects.create(user=self.user_candidate)
        self.token_employer = Token.objects.create(user=self.user_employer)

    def test_job_search(self):
        resp = self.client.get('/api/jobs/search/?q=Backend')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        # support paginated and non-paginated responses
        results = data.get('results') if isinstance(data, dict) and 'results' in data else data
        self.assertTrue(any(j['id'] == self.job.id for j in results))

    def test_resume_upload_and_apply(self):
        resume_content = b"Test resume"
        resume_file = SimpleUploadedFile('resume.txt', resume_content, content_type='text/plain')
        # authenticate as candidate
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_candidate.key)
        upload_resp = self.client.post('/api/resumes/', {'file': resume_file}, format='multipart')
        if upload_resp.status_code != 201:
            print('UPLOAD RESP STATUS', upload_resp.status_code)
            print('UPLOAD RESP CONTENT', upload_resp.content)
        self.assertEqual(upload_resp.status_code, 201)
        resume_id = upload_resp.json().get('id')
        # Apply
        apply_payload = {
            'job': self.job.id,
            'candidate_id': self.candidate.id,
            'resume_id': resume_id,
            'cover_letter': 'Please hire me.',
        }
        apply_resp = self.client.post('/api/applications/create/', apply_payload, format='json')
        self.assertEqual(apply_resp.status_code, 201)
        app_data = apply_resp.json()
        self.assertEqual(app_data['job'], self.job.id)
        self.assertEqual(app_data['candidate']['id'], self.candidate.id)
        self.assertEqual(app_data['status'], 'applied')

    def test_application_status_update_and_notifications(self):
        # Create resume and application
        resume = Resume.objects.create(candidate=self.candidate, file=SimpleUploadedFile('r.txt', b'data'))
        app = Application.objects.create(job=self.job, candidate=self.candidate, resume=resume)
        # Update status
        # authenticate as employer
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token_employer.key)
        resp = self.client.post(f'/api/applications/{app.id}/status/', {'status': 'reviewing'}, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'reviewing')
