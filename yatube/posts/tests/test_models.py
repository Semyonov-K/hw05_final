from django.contrib.auth import get_user_model
from django.test import TestCase
from ..models import Group, Post

User = get_user_model()
COUNT_SYMBOL = 15


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тест пост, такая длинная строка, что скоро пеп8 заругается',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        err_1 = PostModelTest.post.__str__()
        err_2 = PostModelTest.post.text[:COUNT_SYMBOL]
        err_3 = PostModelTest.group.__str__()
        err_4 = PostModelTest.group.title
        self.assertEqual(err_1, err_2, 'post error')
        self.assertEqual(err_3, err_4, 'group error')
