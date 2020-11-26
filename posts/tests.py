import os

from django.conf import settings
from django.core.cache import caches
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post, User

TESTS_CACHE = {
    'default':
    {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

@override_settings(CACHES=TESTS_CACHE)
class TestPostActions(TestCase):
    def setUp(self):
        self.post_data = {
            'text': 'It is test text'
        }

        self.not_auth_user = Client()

        self.user = User.objects.create(
            username='Jack', password='abc12345678',
            email='just_jack@tyler.com'
        )
        self.auth_user = Client()
        self.auth_user.force_login(self.user)
 
    def test_auth_add_new_post(self):
        self.auth_user.post(reverse('new_post'), self.post_data, follow=True)
        post_exist = Post.objects.filter(author=self.user, text=self.post_data['text']).exists()
        self.assertTrue(post_exist)
    
    def test_not_auth_add_new_post(self):
        response = self.not_auth_user.post(reverse('new_post'), self.post_data, follow=True)
        self.assertRedirects(response, '/auth/login/?next=/new/')

    def test_display_new_post(self):
        views = ['new_post', 'profile', 'post_view']

        for view in views:
            if view == 'new_post':
                response = self.auth_user.post(reverse(view), self.post_data, follow=True)
            elif view == 'profile':
                response = self.auth_user.get(reverse(view, args=[self.user.username]))
            else:
                pk = Post.objects.get(text=self.post_data['text']).pk
                response = self.auth_user.get(reverse(view, args=[self.user.username, pk]))

        self.assertContains(response, self.post_data['text'])

    def test_display_edit_post(self):
        views = ['post_edit', 'profile', 'index']
        edit_post_text = {
            'text': 'It is edit test text'
        }

        self.auth_user.post(reverse('new_post'), self.post_data, follow=True)
        pk = Post.objects.get(text=self.post_data['text']).pk

        for view in views:
            if view == 'post_edit':
                response = self.auth_user.post(
                    reverse(view, args=[self.user.username, pk]), 
                    edit_post_text, follow=True
                )
            elif view == 'profile':
                response = self.auth_user.get(reverse(view, args=[self.user.username]))
            else:
                response = self.auth_user.get(reverse(view))
            
            self.assertContains(response, edit_post_text['text'])
    
    def test_404(self):
        response = self.not_auth_user.get(reverse('profile', args=['victor']))
        self.assertEqual(response.status_code, 404)


class TestActionsWithImage(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username='Jack', password='abc12345678',
            email='just_jack@tyler.com'
        )
        self.auth_user = Client()
        self.auth_user.force_login(self.user)

        self.group = Group.objects.create(
            title='group 1', slug='group1',
            description='group 1'
        )

        self.folder_test_files = os.path.join(settings.BASE_DIR, *['posts', 'image_tests'])
    
    def test_display_image(self):
        views = ['new_post', 'group_post', 'post_view', 'profile']
        image_tag = '<img class="card-img"'
        image_path = os.path.join(self.folder_test_files, 'test.jpg')

        for view in views:
            if view == 'new_post':
                with open(image_path, 'rb') as image:
                    data = {
                        'text': 'It is test text',
                        'image': image
                    }
                    response = self.auth_user.post(reverse(view), data, follow=True)
                    post = Post.objects.get(author=self.user)
                    post.group = self.group
                    post.save()
            elif view == 'group_post':
                response = self.auth_user.get(reverse(view, args=[self.group.slug]))
            elif view == 'post_view':
                response = self.auth_user.get(reverse(view, args=[self.user.username, post.pk]))
            else:
                response = self.auth_user.get(reverse('profile', args=[self.user.username]))
            
            self.assertContains(response, image_tag)

    def test_upload_not_image(self):
        file_path = os.path.join(self.folder_test_files, 'test.txt')

        with open(file_path, 'rb') as open_file:
            data = {
                'text': 'It is test text',
                'image': open_file
            }
            self.auth_user.post(reverse('new_post'), data, follow=True)
        post_exist = Post.objects.filter(author=self.user).exists()

        self.assertFalse(post_exist)


class TestProfile(TestCase):
    def setUp(self):
        self.not_auth_user = Client()
        self.user_1 = User.objects.create(
            username='Jack', password='abc12345678', 
            email='just_jack@tyler.com'
        )
        self.auth_user_1 = Client()
        self.auth_user_1.force_login(self.user_1)

        self.user_2 = User.objects.create(
            username='Marla', password='abc12345678', 
            email='marla@tyler.com'
        )

        self.user_3 = User.objects.create(
            username='Tyler', password='abc12345678', 
            email='tyler@tyler.com'
        )
        self.auth_user_3 = Client()
        self.auth_user_3.force_login(self.user_3)
    
    def test_follow_unfollow_user(self):
        self.auth_user_1.get(reverse('profile_follow', args=[self.user_2.username]))
        follow_exist = Follow.objects.filter(user=self.user_1, author=self.user_2).exists()
        self.assertTrue(follow_exist)

        self.auth_user_1.get(reverse('profile_unfollow', args=[self.user_2.username]))
        follow_exist = Follow.objects.filter(user=self.user_1, author=self.user_2).exists()
        self.assertFalse(follow_exist)
    
    def test_dispay_post(self):
        follow = Follow.objects.create(user=self.user_1, author=self.user_2)
        text = 'It is test text'
        post = Post.objects.create(text=text, author=self.user_2)

        response = self.auth_user_1.get(reverse('follow_index'))
        self.assertContains(response, text)

        response = self.auth_user_3.get(reverse('follow_index'))
        self.assertNotContains(response, text)
    
    def test_add_comment(self):
        post = Post.objects.create(text='It is test text', author=self.user_1)
        text = {
            'text': 'It is test comment text'
        }

        response = self.auth_user_1.post(
            reverse('add_comment', args=[post.author.username, post.pk]),
            text, follow=True
        )
        self.assertContains(response, text['text'])

        response = self.not_auth_user.post(
            reverse('add_comment', args=[post.author.username, post.pk]),
            text, follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/Jack/1/comment/')
