from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from smbs_apps.smbs_custom_attrs.models import CustomAttribute


class CustomAttributeTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='pass')
        self.content_type = ContentType.objects.get_for_model(User)

    def test_create_attribute(self):
        attr = CustomAttribute.objects.create(
            content_type=self.content_type,
            object_id=self.user.pk,
            name='color',
            value='blue',
        )
        self.assertEqual(attr.name, 'color')
        self.assertEqual(attr.value, 'blue')

    def test_str_representation(self):
        attr = CustomAttribute.objects.create(
            content_type=self.content_type,
            object_id=self.user.pk,
            name='size',
            value='large',
        )
        self.assertEqual(str(attr), 'size: large')

    def test_content_object_resolves(self):
        attr = CustomAttribute.objects.create(
            content_type=self.content_type,
            object_id=self.user.pk,
            name='role',
            value='admin',
        )
        self.assertEqual(attr.content_object, self.user)

    def test_multiple_attrs_per_object(self):
        for name, value in [('color', 'red'), ('size', 'xl'), ('weight', '2kg')]:
            CustomAttribute.objects.create(
                content_type=self.content_type,
                object_id=self.user.pk,
                name=name,
                value=value,
            )
        attrs = CustomAttribute.objects.filter(
            content_type=self.content_type,
            object_id=self.user.pk,
        )
        self.assertEqual(attrs.count(), 3)
