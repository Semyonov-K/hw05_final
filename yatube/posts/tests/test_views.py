from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post
from ..forms import CommentForm

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='UserTest',
            first_name='Имя',
            last_name='Фамилия',
        )
        cls.group = Group.objects.create(
            title='test-title',
            slug='any-slug',
            description='test-desc',
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='StasBasov')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        post_id = self.post.pk
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:profile',
                    kwargs={'username': 'UserTest'}): 'posts/profile.html',
            reverse('posts:post_edit',
                    kwargs={'post_id':
                            f'{post_id}'}): 'posts/create_post.html',
            reverse('posts:post_detail',
                    kwargs={'post_id':
                            f'{post_id}'}): 'posts/post_detail.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'any-slug'}): 'posts/group_list.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.context['posts'].count(), 1)

    def test_index_paginator(self):
        """Тестирование паджинатора на странице index."""
        for number in range(12):
            Post.objects.create(
                author=self.author,
                text='test-text',
                group=self.group,
            )
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_group_list_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'any-slug'}))
        self.assertEqual(response.context['posts'].count(), 1)

    def test_group_list_paginator(self):
        """Тестирование паджинатора на странице group_list."""
        for number in range(12):
            Post.objects.create(
                author=self.author,
                text='test-text',
                group=self.group,
            )
        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'any-slug'}))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.client.get(
            reverse('posts:group_list',
                    kwargs={'slug': 'any-slug'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_profile_context(self):
        """Шаблон profle сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'UserTest'}))
        self.assertEqual(response.context['num_post_list'], 1)

    def test_profile_paginator(self):
        """Тестирование паджинатора на странице profile."""
        for number in range(12):
            Post.objects.create(
                author=self.author,
                text='test-text',
                group=self.group,
            )
        response = self.client.get(reverse('posts:profile',
                                           kwargs={'username': 'UserTest'}))
        self.assertEqual(len(response.context['page_obj']), 10)

        response = self.client.get(
            reverse('posts:profile',
                    kwargs={'username': 'UserTest'}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_post_detail_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.context['post'].text, 'test-text')
        self.assertEqual(response.context['post'].group, self.post.group)
        self.assertEqual(response.context['post'].author, self.author)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
