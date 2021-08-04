from smbs_comments_tree.forms import CommentForm

from smbs_qa.models import QuestionComment


class QuestionCommentForm(CommentForm):

    class Meta(CommentForm.Meta):
        model = QuestionComment
