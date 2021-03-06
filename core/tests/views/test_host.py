import urllib.parse

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission

from core import models
from core.views import host
from core.tests.factories import create_data_for_search_host
from core.tests.mixins import TestDefaultMixin


class SearchHostView(TestDefaultMixin, TestCase):

    def setUp(self):
        self.user = User.objects.create(
            username='Serega',
            password='passwd',
        )
        self.pem = 'view_host'
        self.user.user_permissions.add(Permission.objects.get(codename=self.pem))
        self.url = reverse('host_search')

    def test_permissions_mixin(self):
        self.user.user_permissions.remove(Permission.objects.get(codename='view_host'))

        self.client.force_login(user=self.user)
        http_referer = 'http://127.0.0.1/hosts'
        response = self.client.get(reverse('host_search'), HTTP_REFERER=http_referer)
        url = reverse('permission_denied') + '?next=%s' % urllib.parse.quote(http_referer)

        self.assertRedirects(response, url)

    def test_get_queryset(self):
        create_data_for_search_host()

        self.client.force_login(user=self.user)
        response = self.client.get(reverse('host_search'),
                                   {'name': 'Test', 'address': '192.168.19.19', 'group': 1})

        self.assertEqual(len(response.context['object_list']), 2)

    def test_paginate(self):
        create_data_for_search_host()

        self.client.force_login(user=self.user)
        response = self.client.get(reverse('host_search'), {'paginate_by': '1'})

        self.assertEqual(len(response.context['object_list']), 1)

    def test_paginate_all(self):
        create_data_for_search_host()

        self.client.force_login(user=self.user)
        response = self.client.get(reverse('host_search'), {'paginate_by': '-1'})

        self.assertEqual(len(response.context['object_list']), 3)

    def test_context(self):
        self.client.force_login(user=self.user)
        response = self.client.get(reverse('host_search'))

        self.assertEqual(response.context['breadcrumbs'][0], ('Home', reverse('index')))
        self.assertEqual(response.context['breadcrumbs'][1], (host.Search.title, ''))


class EditHostView(TestDefaultMixin, TestCase):

    def setUp(self):
        self.user = User.objects.create(
            username='Serega',
            password='passwd',
        )
        self.pem = 'add_host'
        self.url = reverse('host_create')
        self.user.user_permissions.add(Permission.objects.get(codename='add_host'))
        models.HostGroup.objects.create(
            name='Test name',
        )

    def test_create(self):
        self.user.user_permissions.add(Permission.objects.get(codename='view_host'))
        self.client.force_login(user=self.user)

        response = self.client.post(reverse('host_create'),
                                    {'address': '192.168.19.19', 'form-INITIAL_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                                     'form-MIN_NUM_FORMS': '0', 'form-TOTAL_FORMS': '1', 'groups': '1',
                                     'name': 'Test name'})

        self.assertEqual(str(models.Host.objects.get(id=1)), 'Test name (192.168.19.19)')
        self.assertRedirects(response, reverse('host_search'))

    def test_create_invalid(self):
        self.client.force_login(user=self.user)

        response = self.client.post(reverse('host_create'),
                                    {'address': '  ', 'form-INITIAL_FORMS': '0', 'form-MAX_NUM_FORMS': '1000',
                                     'form-MIN_NUM_FORMS': '0', 'form-TOTAL_FORMS': '1', 'groups': '1',
                                     'name': 'Test name'})

        self.assertContains(response, 'This field is required.')

    def test_edit(self):
        self.user.user_permissions.add(Permission.objects.get(codename='view_host'))
        host = models.Host.objects.create(
            name='Test',
            address='192.168.19.19'
        )
        models.HostGroup.objects.create(
            name='Other test name'
        )
        host.groups.add(models.HostGroup.objects.get(name='Test name'))

        self.client.force_login(user=self.user)
        response = self.client.post(reverse('host_update', args=['1']),
                                    {'address': '192.168.19.18', 'form-INITIAL_FORMS': '0',
                                     'form-MAX_NUM_FORMS': '1000', 'form-MIN_NUM_FORMS': '0', 'form-TOTAL_FORMS': '1',
                                     'groups': '2', 'name': 'Test Test'})
        changed_host = models.Host.objects.get(id=1)

        self.assertEqual(str(changed_host), 'Test Test (192.168.19.18)')
        self.assertEqual(str(changed_host.groups.get(id=2)), 'Other test name')
        self.assertRedirects(response, reverse('host_search'))

    def test_edit_invalid(self):
        host = models.Host.objects.create(
            name='Test',
            address='192.168.19.19'
        )
        models.HostGroup.objects.create(
            name='Other test name'
        )
        host.groups.add(models.HostGroup.objects.get(name='Test name'))

        self.client.force_login(user=self.user)

        response = self.client.post(reverse('host_update', args=['1']),
                                    {'address': '  ', 'form-INITIAL_FORMS': '0',
                                     'form-MAX_NUM_FORMS': '1000', 'form-MIN_NUM_FORMS': '0', 'form-TOTAL_FORMS': '1',
                                     'groups': '2', 'name': 'Test Test'})

        self.assertContains(response, 'This field is required.')

    def test_context_create(self):
        self.client.force_login(user=self.user)

        response = self.client.get(reverse('host_create'))

        self.assertEqual(response.context['breadcrumbs'][0], ('Home', reverse('index')))
        self.assertEqual(response.context['breadcrumbs'][1], (host.Search.title, reverse('host_search')))
        self.assertEqual(response.context['breadcrumbs'][2], (host.Edit.title_create, ''))

    def test_context_update(self):
        models.Host.objects.create(
            name='Test',
            address='192.168.19.19'
        )
        self.client.force_login(user=self.user)

        response = self.client.get(reverse('host_update', args=['1']))

        self.assertEqual(response.context['breadcrumbs'][2], (str(models.Host.objects.get(pk=1)), ''))


class DeleteHostView(TestDefaultMixin, TestCase):

    def setUp(self):
        self.user = User.objects.create(
            username='Serega',
            password='passwd',
        )
        self.pem = 'delete_host'
        self.url = reverse('host_delete', args='1')
        self.user.user_permissions.add(Permission.objects.get(codename='delete_host'))
        self.user.user_permissions.add(Permission.objects.get(codename='view_host'))
        models.Host.objects.create(
            name='Test',
            address='192.168.19.19'
        )

    def test_delete_host(self):
        self.client.force_login(user=self.user)

        response = self.client.post(reverse('host_delete', args=['1']))

        self.assertEqual(len(models.Host.objects.all()), 0)
        self.assertRedirects(response, reverse('host_search'))
