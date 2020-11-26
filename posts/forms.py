from django import forms

from posts.models import Comment, Group, Post


class PostForm(forms.ModelForm):
    class Meta:
            model = Post
            fields = ('text', 'group', 'image')

            labels = {
                'text':  'Введите текст поста',
                'group': 'Выберите группу'
            }
            
            widgets = {
                'text': forms.Textarea
            }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text', )

        widgets = {
            'text': forms.Textarea
        }
