from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth.models import User

from smbs_apps.smbs_qa.models import Question, QuestionComment


class QuestionTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='asker', password='pass')

    def _make_question(self, title='How does Django work?', **kwargs):
        q = Question(
            site=self.site,
            user=self.user,
            title=title,
            question='Can you explain the MTV pattern?',
            **kwargs,
        )
        q.clean()
        q.save()
        return q

    def test_clean_generates_slug(self):
        q = Question(
            site=self.site,
            user=self.user,
            title='What is Python?',
            question='Tell me about Python.',
        )
        q.clean()
        self.assertEqual(q.slug, 'what-is-python')

    def test_slug_handles_special_characters(self):
        q = Question(
            site=self.site,
            user=self.user,
            title='How do I use Django ORM?',
            question='ORM question',
        )
        q.clean()
        self.assertNotIn(' ', q.slug)
        self.assertNotIn('?', q.slug)

    def test_is_anonymous_default_false(self):
        q = self._make_question()
        self.assertFalse(q.is_anonymous)

    def test_anonymous_question(self):
        q = self._make_question(is_anonymous=True)
        self.assertTrue(q.is_anonymous)

    def test_create_question_saves(self):
        q = self._make_question()
        self.assertIsNotNone(q.pk)
        self.assertEqual(q.user, self.user)


class QuestionCommentTest(TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()
        self.user = User.objects.create_user(username='commenter', password='pass')
        question = Question(
            site=self.site,
            user=self.user,
            title='Test question',
            question='A question body.',
        )
        question.clean()
        question.save()
        self.question = question

    def test_create_comment(self):
        comment = QuestionComment.objects.create(
            question=self.question,
            user=self.user,
            text='This is my answer.',
        )
        self.assertEqual(comment.question, self.question)
        self.assertFalse(comment.deleted)

    def test_get_absolute_url_contains_question_id(self):
        comment = QuestionComment.objects.create(
            question=self.question,
            user=self.user,
            text='Answer here.',
        )
        url = comment.get_absolute_url()
        self.assertIn(str(self.question.id), url)
