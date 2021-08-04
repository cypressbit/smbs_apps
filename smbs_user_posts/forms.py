from smbs_comments_tree.forms import CommentForm

from smbs_user_posts.models import UserPostComment


class UserPostCommentForm(CommentForm):

    class Meta(CommentForm.Meta):
        model = UserPostComment
