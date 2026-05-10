# search/tests/test_staff_profile_search.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from kiini.models.staff import StaffProfile
from kiini.models.institution import Institution
from kiini.models.department import Department
from search.documents.staff_profile_document import StaffProfileDocument

User = get_user_model()

@pytest.mark.django_db
class TestStaffProfileSearch:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = APIClient()
        self.conn = connections.get_connection()

        self.institution = Institution.objects.create(name='Jamiikazini Tech')
        self.department = Department.objects.create(name='ICT', institution=self.institution)
        self.user = User.objects.create_user(username='janedoe', email='jane@example.com', password='pass1234')
        self.profile = StaffProfile.objects.create(
            user=self.user,
            institution=self.institution,
            department=self.department,
            position='Developer',
            title='Senior Dev',
            phone='0712345678',
            is_active=True,
        )

        # Indexing manually
        doc = StaffProfileDocument()
        doc.update(doc.get_queryset())

    def test_can_search_staff_profile_by_position(self):
        response = self.client.get('/search/staff-profiles/', {'search': 'Developer'})
        assert response.status_code == 200
        assert response.data['count'] >= 1
        assert any('Developer' in result['position'] for result in response.data['results'])

    def test_filter_by_institution_id(self):
        response = self.client.get('/search/staff-profiles/', {'institution_id': self.institution.id})
        assert response.status_code == 200
        assert all(result['institution']['id'] == self.institution.id for result in response.data['results'])

    def test_filter_by_active_status(self):
        response = self.client.get('/search/staff-profiles/', {'is_active': True})
        assert response.status_code == 200
        assert all(result['is_active'] for result in response.data['results'])