
class ReactionMixin:

    def get_reactions(self):
        reaction_count = self.reactions.count()
        reactions = self.reactions.values('reaction').distinct()
        return {
            'reaction_count': reaction_count,
            'reactions': reactions
        }
