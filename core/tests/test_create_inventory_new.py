import mock
import os
import shutil

from django.contrib.auth.models import User
from django.test import TestCase, override_settings

from core import models
from core.datatools import ansible, tasks


class Ansible(TestCase):

    def setUp(self):
        ansible_user = models.AnsibleUser.objects.create(
            name='Serega'
        )
        self.user = User.objects.create(
            username='Serega',
            password='passwd'
        )
        task_template = models.TaskTemplate.objects.create(
            name='qwer',
            playbook='/home/',
        )
        empty_host_group = models.HostGroup.objects.create(
            name="Empty test host_group",
        )
        task2 = models.Task.objects.create(
            playbook="/home2/",
            template=task_template,
            user=self.user,
            ansible_user=ansible_user,
        )
    @mock.patch('core.datatools.ansible.tempfile.mkdtemp')
    def test_create_inventory(self, tempfile_mock):
        test_path_tempfile = '/tmp/test'
        tempfile_mock.return_value = test_path_tempfile
        if os.path.exists(test_path_tempfile):
            shutil.rmtree(test_path_tempfile)
        os.mkdir(test_path_tempfile)

        self.assertRaises(Exception, ansible.create_inventory, models.Task.objects.get(playbook='/home2/'))
        shutil.rmtree(test_path_tempfile)
