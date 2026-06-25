from django.test import TestCase
from django.contrib.auth.models import User

from smbs_apps.smbs_reactions.models import Reaction
from smbs_apps.smbs_reactions.mixins import ReactionMixin


class ReactionModelTest(TestCase):
    def test_is_abstract(self):
        self.assertTrue(Reaction._meta.abstract)

    def test_reaction_choices_defined(self):
        choices = [r[0] for r in Reaction.REACTIONS]
        self.assertIn(Reaction.THUMBS_UP, choices)
        self.assertIn(Reaction.THUMBS_DOWN, choices)
        self.assertIn(Reaction.ANGRY, choices)
        self.assertIn(Reaction.SAD, choices)
        self.assertIn(Reaction.HAPPY, choices)

    def test_default_reaction_is_thumbs_up(self):
        field = Reaction._meta.get_field('reaction')
        self.assertEqual(field.default, Reaction.THUMBS_UP)


class ReactionMixinTest(TestCase):
    def test_get_reactions_interface(self):
        mixin = ReactionMixin()
        self.assertTrue(hasattr(mixin, 'get_reactions'))
