from django.test import TestCase

from smbs_apps.smbs_accounts.forms import SMBSUserCreationForm


class SMBSUserCreationFormTest(TestCase):
    def _valid_data(self, **overrides):
        data = {
            'username': 'newuser',
            'email': 'user@example.com',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'password1': 'Str0ngP@ssword!',
            'password2': 'Str0ngP@ssword!',
        }
        data.update(overrides)
        return data

    def test_valid_form(self):
        form = SMBSUserCreationForm(data=self._valid_data())
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_required(self):
        form = SMBSUserCreationForm(data=self._valid_data(email=''))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_first_name_required(self):
        form = SMBSUserCreationForm(data=self._valid_data(first_name=''))
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_last_name_required(self):
        form = SMBSUserCreationForm(data=self._valid_data(last_name=''))
        self.assertFalse(form.is_valid())
        self.assertIn('last_name', form.errors)

    def test_password_mismatch(self):
        form = SMBSUserCreationForm(data=self._valid_data(password2='DifferentPass!'))
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_form_fields_have_form_control_class(self):
        form = SMBSUserCreationForm()
        self.assertEqual(
            form.fields['username'].widget.attrs.get('class'), 'form-control'
        )
        self.assertEqual(
            form.fields['email'].widget.attrs.get('class'), 'form-control'
        )
