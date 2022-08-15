import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Comment, Group, Post
from ..forms import PostForm


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='UserTest',
            first_name='Имя',
            last_name='Фамилия',
        )
        cls.author_2 = User.objects.create_user(
            username='UserTest_2',
            first_name='Имя',
            last_name='Фамилия',
        )
        cls.author_3 = User.objects.create_user(
            username='UserTest_3',
            first_name='Имя',
            last_name='Фамилия',
        )
        cls.group = Group.objects.create(
            title='test-title',
            slug='any-slug',
            description='test-desc',
        )
        cls.group_two = Group.objects.create(
            title='test-title-two',
            slug='any-slug-two',
            description='test-desc-two',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='test-text',
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='UserTest1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.author_2)
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(self.author_3)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        Post.objects.create(
            text='test_new_post',
            author=self.author,
        )
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)

    def test_create_post_base(self):
        """Создание поста."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.post.text,
            'author': self.author.id,
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.author}))

    def test_edit_post(self):
        """Проверка редактирования поста"""
        edit_post = {
            'text': 'test-text-redactiruemii-po-angliski',
            'group': self.group_two.id
        }
        edit_post_id = Post.objects.get(id=self.post.id)
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': f'{self.post.id}'}),
            data=edit_post,
            follow=True,
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': f'{self.post.id}'}))
        self.assertNotEqual(edit_post_id.text, edit_post['text'])
        self.assertNotEqual(edit_post_id.group.id, edit_post['group'])

    def test_edit_post_guest(self):
        """Неавторизованный пользователь не может редактировать пост."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'test-text-redactiruemii-po-angliski',
            'group': self.group_two.id,
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{self.post.id}/edit/')

    def test_image_in_all(self):
        """Проверка картинки в словаре в разделах и создалась ли запись."""
        form_data = {
            'text': self.post.text,
            'author': self.author,
            'group': self.group,
            'image': self.uploaded
        }

        response = self.authorized_client.get(
            reverse('posts:index'),
            data=form_data,
            follow=True
        )
        context_profile_image = response.context.get('posts')[0].image
        expected_image = self.post.image
        self.assertEqual(context_profile_image, expected_image)

        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author}),
            data=form_data,
            follow=True
        )
        context_profile_image = response.context.get('page_obj')[0].image
        expected_image = self.post.image
        self.assertEqual(context_profile_image, expected_image)

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            data=form_data,
            follow=True
        )
        context_profile_image = response.context.get('posts')[0].image
        expected_image = self.post.image
        self.assertEqual(context_profile_image, expected_image)

        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        context_profile_image = response.context.get('post').image
        expected_image = self.post.image
        self.assertEqual(context_profile_image, expected_image)

        self.assertTrue(
            Post.objects.filter(
                text=self.post.text,
                author=self.author,
                group=self.group,
                image='posts/small.gif'
            ).exists()
        )

    def test_comment_guest_client(self):
        """Неавторизованный пользователь не может комментировать посты."""
        try_comment = {
            'text': 'test comment',
        }
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    kwargs={'post_id': f'{self.post.id}'}),
            data=try_comment,
            follow=True,
        )
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts/{self.post.id}/comment/'
        )

    def test_comment(self):
        """Комментарии создается и появляется на странице поста"""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'atyatya',
            'author': self.author_2,
        }
        response = self.authorized_client_2.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertRedirects(
            response,
            reverse('posts:post_detail',
            kwargs={'post_id': self.post.id}
            )
        )
        self.assertTrue(Comment.objects.filter(
            text='atyatya',
            author=self.author_2,)
        )

    def test_follow_and_unfollow(self):
        """Подписка и отписка."""
        Follow.objects.create(user=self.author, author=self.author_2)
        self.assertEqual(Follow.objects.all().count(), 1)
        Follow.objects.filter(user=self.author, author=self.author_2).delete()
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_new_post_for_follower(self):
        """Посты появляются у фолловеров, и не появляются у нефолловеров."""
        Follow.objects.create(user=self.author, author=self.author_2)
        form_data = {
            'text': self.post.text,
            'author': self.author.id,
            'group': self.group.id
        }
        new_post = self.authorized_client_2.post(
            reverse('posts:post_create'),
            data=form_data,
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_text = response.context.get('page_obj')[0].text
        self.assertEqual(self.post.text, post_text)
        response = self.authorized_client_3.get(reverse('posts:follow_index'))
        post_text = response.context.get('page_obj')
        self.assertNotIn(new_post, post_text)
