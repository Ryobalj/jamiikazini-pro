# homepage/tests/test_homepage.py

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient

from homepage.models.home_page import HomePage
from homepage.models.hero_section import HeroSection

# 1x1 px GIF halisi - ndogo kabisa inayokubalika na Pillow/ImageField
TINY_GIF = (
    b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00'
    b'\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
)


def _dummy_image(name='test.gif'):
    return SimpleUploadedFile(name, TINY_GIF, content_type='image/gif')
from homepage.models.about_section import AboutSection


@pytest.mark.django_db
def test_get_or_create_for_institution(institution_factory):
    institution = institution_factory()
    homepage = HomePage.get_or_create_for(institution)

    assert homepage.owner == institution
    assert homepage.name == institution.name

    # idempotent - haiundi nyingine
    again = HomePage.get_or_create_for(institution)
    assert again.id == homepage.id
    assert HomePage.objects.count() == 1


@pytest.mark.django_db
def test_is_owned_by(institution_factory, user_factory):
    owner = user_factory()
    stranger = user_factory()
    institution = institution_factory(owner=owner)
    homepage = HomePage.get_or_create_for(institution)

    assert homepage.is_owned_by(owner) is True
    assert homepage.is_owned_by(stranger) is False


@pytest.mark.django_db
def test_my_homepage_view_owner_can_get_and_patch(institution_factory, user_factory):
    owner = user_factory()
    institution = institution_factory(owner=owner)

    client = APIClient()
    client.force_authenticate(user=owner)

    url = reverse('homepage:my-homepage', kwargs={'owner_type': 'institution', 'owner_id': institution.id})
    response = client.get(url)
    assert response.status_code == 200, response.content
    assert response.json()['name'] == institution.name

    patch_response = client.patch(url, {'tagline': 'Huduma bora'}, format='json')
    assert patch_response.status_code == 200, patch_response.content
    assert patch_response.json()['tagline'] == 'Huduma bora'


@pytest.mark.django_db
def test_my_homepage_view_rejects_non_owner(institution_factory, user_factory):
    owner = user_factory()
    stranger = user_factory()
    institution = institution_factory(owner=owner)

    client = APIClient()
    client.force_authenticate(user=stranger)

    url = reverse('homepage:my-homepage', kwargs={'owner_type': 'institution', 'owner_id': institution.id})
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_public_homepage_hidden_until_published(institution_factory):
    institution = institution_factory()
    homepage = HomePage.get_or_create_for(institution)
    homepage.is_published = False
    homepage.save()

    client = APIClient()
    url = reverse('homepage:public-homepage', kwargs={'owner_type': 'institution', 'owner_id': institution.id})
    assert client.get(url).status_code == 404

    homepage.is_published = True
    homepage.save()
    response = client.get(url)
    assert response.status_code == 200
    assert response.json()['name'] == institution.name


@pytest.mark.django_db
def test_public_homepage_only_shows_active_sections(institution_factory):
    institution = institution_factory()
    homepage = HomePage.get_or_create_for(institution)
    HeroSection.objects.create(homepage=homepage, title='Active Hero', is_active=True)
    HeroSection.objects.create(homepage=homepage, title='Hidden Hero', is_active=False)

    client = APIClient()
    url = reverse('homepage:public-homepage', kwargs={'owner_type': 'institution', 'owner_id': institution.id})
    data = client.get(url).json()

    titles = [h['title'] for h in data['hero_sections']]
    assert titles == ['Active Hero']


@pytest.mark.django_db
def test_owner_can_create_hero_section_non_owner_cannot(institution_factory, user_factory):
    owner = user_factory()
    stranger = user_factory()
    institution = institution_factory(owner=owner)
    homepage = HomePage.get_or_create_for(institution)

    url = reverse('homepage:homepage-hero-list', kwargs={'homepage_pk': homepage.id})

    client = APIClient()
    client.force_authenticate(user=owner)
    response = client.post(url, {'title': 'Karibu Jamiikazini'}, format='json')
    assert response.status_code == 201, response.content
    assert HeroSection.objects.filter(homepage=homepage).count() == 1

    client.force_authenticate(user=stranger)
    response = client.post(url, {'title': 'Jaribio la wizi'}, format='json')
    assert response.status_code == 403
    assert HeroSection.objects.filter(homepage=homepage).count() == 1


@pytest.mark.django_db
def test_owner_can_add_about_image_non_owner_cannot(institution_factory, user_factory):
    owner = user_factory()
    stranger = user_factory()
    institution = institution_factory(owner=owner)
    homepage = HomePage.get_or_create_for(institution)
    about = AboutSection.objects.create(homepage=homepage, description='Sisi ni akina nani')

    url = reverse('homepage:about-image-list', kwargs={'homepage_pk': homepage.id, 'about_pk': about.id})

    client = APIClient()
    client.force_authenticate(user=stranger)
    response = client.post(url, {'caption': 'jaribio', 'image': _dummy_image()}, format='multipart')
    assert response.status_code == 403

    client.force_authenticate(user=owner)
    response = client.post(url, {'caption': 'Ofisi yetu', 'image': _dummy_image()}, format='multipart')
    assert response.status_code == 201, response.content
    assert about.gallery.count() == 1


@pytest.mark.django_db
def test_business_can_also_own_a_homepage(business_factory, user_factory):
    owner = user_factory()
    business = business_factory(owner=owner)
    homepage = HomePage.get_or_create_for(business)

    assert homepage.owner == business
    assert homepage.is_owned_by(owner) is True

    client = APIClient()
    client.force_authenticate(user=owner)
    url = reverse('homepage:my-homepage', kwargs={'owner_type': 'business', 'owner_id': business.id})
    response = client.get(url)
    assert response.status_code == 200, response.content
