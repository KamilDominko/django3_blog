from django.shortcuts import render, get_object_or_404
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from .forms import EmailPostForm, CommentForm
from django.core.mail import send_mail
from mysite import email_data as ed
from taggit.models import Tag
from django.db.models import Count


class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_list(request, tag_slug=None):
    object_list = Post.published.all()
    tag = None

    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])

    paginator = Paginator(object_list, 3)  # Trzy posty na każdej stronie.
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        # Jeżeli zmienna page nie jest liczbą całkowitą,
        # wówczas pobierana jest pierwsza strona wyników.
        posts = paginator.page(1)
    except EmptyPage:
        # Jeżelli zmienna page ma wartość większą niż numer ostatniej strony
        # wyników, wtedy pobierana jest ostatnia strona wyników.
        posts = paginator.page(paginator.num_pages)
    context = {'posts': posts, 'page': page, 'tag': tag}
    return render(request, 'blog/post/list.html', context)


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             slug=post,
                             status='published',
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # Lista aktywnych komentarzy dla danego posta.
    comments = post.comments.filter(active=True)

    if request.method == 'POST':
        # Komentarz został opublikowany.
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Utworzenie obiektu Comment ALE nie zapisujemy go w bazie danych.
            new_comment = comment_form.save(commit=False)
            # Przypisanie komentarza do bierzącego posta.
            new_comment.post = post
            # Zapisanie komentarza w bazie danych.
            new_comment.save()
    else:
        comment_form = CommentForm()

    # Lista podobnych postów.
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids). \
        exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')). \
                        order_by('-same_tags', '-publish')[:4]

    context = {'post': post, 'comments': comments, 'comment_form': comment_form,
               'similar_posts': similar_posts}
    return render(request, 'blog/post/detail.html', context)


def post_share(request, post_id):
    # Pobieranie posta na podstawie jego identyfikatora.
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False

    if request.method == 'POST':
        # Formularz został wysłany.
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Weryfikacja pól formularza zakończyła się powodzeniem...
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            # subject = ('{} ({}) zachęca do przeczytania "{}"'.
            #            format(cd['name'], cd['email'], post.title))
            # message = ('Przeczytaj post "{}" na stronie {}\n\n'
            #            'Komentarz dodany przez {}: {}'.
            #            format(post.title, post_url, cd['name'], cd['comments']))
            subject = (f'{cd["name"]} ({cd["email"]}) zachęca do przeczytania '
                       f'"{post.title}"')
            message = (
                f'Przeczytaj post "{post.title}" na stronie {post_url}\n\n'
                f'Komentarz dodany przez {cd["name"]}: {cd["comments"]}')
            send_mail(subject, message, ed.EMAIL_HOST_USER, [cd['to']])
            sent = True
            # ...więc można wysłać wiadomość
    else:
        form = EmailPostForm()
    context = {'post': post, 'form': form, 'sent': sent}
    return render(request, 'blog/post/share.html', context)
