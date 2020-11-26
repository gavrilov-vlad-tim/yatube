from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User


class TestSignupPostEdit(TestCase):
    def setUp(self):
        self.not_auth_user = Client()   
        self.user_data = {
            'username': 'Jack',
            'password1': 'MarTyJ202',
            'email': 'just_jack@tyler.com',
            'password2': 'MarTyJ202'
        }
        self.not_auth_user.post(reverse('signup'), self.user_data, follow=True)

    def test_signup(self):

        try:
            user = User.objects.get(email=self.user_data['email'])
        except User.DoesNotExist:
            user = None
        self.not_auth_user.force_login(user)
        response = self.not_auth_user.get(reverse('profile', args=[user.username]))
        self.assertEqual(response.status_code, 200)