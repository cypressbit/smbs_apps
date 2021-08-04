from taggit.forms import TagWidget

from django import forms
from django.utils.text import slugify
from django.contrib.sites.models import Site

from smbs_blog.models import Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = (
            'author',
            'publish_date',
            'language',
            'site',
            'title',
            'cover_image',
            'content',
            'description',
            'tags',
            'is_draft',
            'slug',
        )

        widgets = {
            'author': forms.TextInput(attrs={'hidden': True}),
            'publish_date': forms.DateTimeInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'site': forms.Select(attrs={'hidden': True, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'hidden': True}),
            'cover_image': forms.FileInput(attrs={'class': 'custom-file-input'}),
            'content': forms.Textarea(attrs={'hidden': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'cols': 100, 'rows': 3}),
            'tags': TagWidget(attrs={'class': 'form-control'}),
            'is_draft': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'slug': forms.TextInput(attrs={'hidden': True, 'class': 'form-control'}),
        }

    def clean_slug(self):
        title = self.cleaned_data['title']
        return slugify(title)

    def clean_site(self):
        return Site.objects.get_current()
