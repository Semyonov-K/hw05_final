from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from posts.models import Post, Group

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
        self.guest_client = Client()
        self.user = User.objects.create_user(username='anyname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_url_for_all(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_slug_url_for_all(self):
        """Страница group/slug доступна любому пользователю."""
        response = self.guest_client.get('/group/any-slug/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_username_url_for_all(self):
        """Страница profile/username доступна любому пользователю."""
        response = self.guest_client.get('/profile/UserTest/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_post_id_username_url_for_all(self):
        """Страница posts/post_id доступна любому пользователю."""
        post_id = self.post.pk
        response = self.guest_client.get(f'/posts/{post_id}/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_for_auth_people(self):
        """Страница create доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_for_author(self):
        """Страница post/edit доступна автору."""
        if self.post.author == self.author.username:
            post_id = self.post.pk
            response = self.authorized_client.get(f'/posts/{post_id}/edit')
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_return_404(self):
        """Запрос к несуществующей странице вернёт ошибку 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        if self.post.author == self.author.username:
            post_id = self.post.pk
            templates_url_names = {
                '/group/any-slug/': 'posts/group_list.html',
                '/profile/UserTest/': 'posts/profile.html',
                f'/posts/{post_id}': 'posts/post_detail.html',
                '/create/': 'posts/create_post.html',
                f'posts/{post_id}/edit/': 'posts/create_post.html',
                '/': 'posts/index.html',
                '/lol/': 'core/404.html'
            }
            for address, template in templates_url_names.items():
                with self.subTest(template=template):
                    response = self.authorized_client.get(template)
                    self.assertTemplateUsed(response, address)
