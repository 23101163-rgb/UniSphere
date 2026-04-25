from django import forms
from .models import Thread, Reply

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title', 'content', 'image', 'category']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs['class'] = 'form-control'
        self.fields['content'].widget = forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': "What's on your mind?"})
        self.fields['title'].widget.attrs['placeholder'] = 'Post title...'

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ['content']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].widget.attrs.update({'class': 'form-control', 'rows': 2, 'placeholder': 'Write a comment...'})