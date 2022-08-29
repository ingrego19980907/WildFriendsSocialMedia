import random
from datetime import datetime, date, timedelta
from string import Formatter

from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Post, LikePost, FollowersCount
from itertools import chain


def strfdelta(tdelta, fmt='{D:02}d {H:02}h {M:02}m {S:02}s', inputtype='timedelta'):

    # Convert tdelta to integer seconds.
    if inputtype == 'timedelta':
        remainder = int(tdelta.total_seconds())
    elif inputtype in ['s', 'seconds']:
        remainder = int(tdelta)
    elif inputtype in ['m', 'minutes']:
        remainder = int(tdelta)*60
    elif inputtype in ['h', 'hours']:
        remainder = int(tdelta)*3600
    elif inputtype in ['d', 'days']:
        remainder = int(tdelta)*86400
    elif inputtype in ['w', 'weeks']:
        remainder = int(tdelta)*604800
    elif inputtype in ['Mth', 'month']:
        remainder = int(tdelta) * 2629743
    elif inputtype in ['Y', 'month']:
        remainder = int(tdelta) * 31556926


    f = Formatter()
    desired_fields = [field_tuple[1] for field_tuple in f.parse(fmt)]
    possible_fields = ('Y', 'Mth', 'W', 'D', 'H', 'M', 'S')
    constants = {'Y': 31556926, 'Mth': 2629743, 'W': 604800, 'D': 86400, 'H': 3600, 'M': 60, 'S': 1}
    values = {}
    for field in possible_fields:
        if field in desired_fields and field in constants:
            values[field], remainder = divmod(remainder, constants[field])
    return f.format(fmt, **values)


@login_required(login_url='signin')
def index(request):
    all_users = User.objects.all()
    all_profiles = Profile.objects.all()
    user_object = all_users.get(username=request.user.username)
    user_profile = all_profiles.get(user=user_object)

    user_following_list = []
    feed = []

    user_following = FollowersCount.objects.filter(follower=request.user.username)

    for users in user_following:
        user_following_list.append(users.user)

    for username in user_following_list:
        feed_lists = Post.objects.filter(user=username)
        post_maker_user_obj = all_users.get(username=username)
        post_maker_profile = all_profiles.get(user=post_maker_user_obj)

        for feed_list in feed_lists:
            make_post_time_ago = timedelta(seconds=(datetime.timestamp(datetime.now()) - datetime.timestamp(feed_list.created_at) + 10800))

            if make_post_time_ago > timedelta(days=730):
                message = f"{strfdelta(make_post_time_ago, '{Y} year')} ago"
            elif make_post_time_ago > timedelta(days=365):
                message = f"{strfdelta(make_post_time_ago, '{Y} year')} ago"
            elif make_post_time_ago > timedelta(days=60):
                message = f"{strfdelta(make_post_time_ago, '{Mth} month')} ago"
            elif make_post_time_ago > timedelta(days=31):
                message = f"{strfdelta(make_post_time_ago, '{Mth} month')} ago"
            elif make_post_time_ago > timedelta(days=2):
                message = f"{strfdelta(make_post_time_ago, '{D} days')} ago"
            elif make_post_time_ago > timedelta(days=1):
                message = f"{strfdelta(make_post_time_ago, '{D} day')} ago"
            elif make_post_time_ago > timedelta(hours=2):
                message = f"{strfdelta(make_post_time_ago, '{H} hours')} ago"
            elif make_post_time_ago > timedelta(hours=1):
                message = f"{strfdelta(make_post_time_ago, '{H} hour')} ago"
            elif make_post_time_ago > timedelta(minutes=2):
                message = f"{strfdelta(make_post_time_ago, '{M} minutes')} ago"
            elif make_post_time_ago > timedelta(minutes=1):
                message = f"{strfdelta(make_post_time_ago, '{M} minute')} ago"
            else:
                message = f"less then minute"
            feed.append((feed_list, post_maker_profile, message))

    # feed_list = list(chain(*feed))
    # print('+++++++++++', feed_list)
    # user suggestion starts
    user_following_all = []

    for user in user_following:
        user_list = all_users.get(username=user.user)
        user_following_all.append(user_list)

    new_suggestions_list = [x for x in list(all_users) if (x not in list(user_following_all))]
    current_user = all_users.filter(username=request.user.username)
    final_suggestions_list = [x for x in list(new_suggestions_list) if (x not in list(current_user))]
    random.shuffle(final_suggestions_list)

    username_profile = []
    username_profile_list = []

    for users in final_suggestions_list:
        username_profile.append(users.id)

    for ids in username_profile:
        profile_lists = all_profiles.filter(id_user=ids)
        username_profile_list.append(profile_lists)

    suggestion_username_profile_list = list(chain(*username_profile_list))

    context = {
        "title": "Home",
        "user_profile": user_profile,
        "posts": feed,
        "suggestion_username_profile_list": suggestion_username_profile_list[:4],
    }
    return render(request, 'index.html', context)


@login_required(login_url='signin')
def settings(request):
    user_profile = Profile.objects.get(user=request.user)
    context = {
        'user_profile': user_profile,
    }
    if request.method == 'POST':
        if request.FILES.get('image') == None:
            image = user_profile.profileimg
        else:
        # if request.FILES.get('image') != None:
            image = request.FILES.get('image')

        bio = request.POST['bio']
        location = request.POST['location']

        user_profile.profileimg = image
        user_profile.bio = bio
        user_profile.location = location
        user_profile.save()
        return redirect('settings')

    return render(request, 'setting.html', context)


def signup(request):
    context = {"title": "Signup"}
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('signup')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()

                # Log user in and redirect to settings page
                user_login = auth.authenticate(username=username, password=password)
                auth.login(request, user_login)

                # create profile for a new user
                user_model = User.objects.get(username=username)
                new_profile = Profile.objects.create(user=user_model, id_user=user_model.id)
                new_profile.save()
                return redirect('settings')
        else:
            messages.info(request, "Password Not Valid")
            return redirect('signup')
    else:
        return render(request, 'signup.html', context)


def signin(request):
    context = {
        'title': "Sign In"
    }
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('/')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('signin')

    else:
        return render(request, 'signin.html', context)


@login_required(login_url='signin')
def logout(request):
    auth.logout(request)
    return redirect('signin')


@login_required(login_url='signin')
def upload(request):
    if request.method == 'POST':
        user = request.user.username
        image = request.FILES.get('image_upload')
        caption = request.POST['caption']

        new_post = Post.objects.create(user=user, image=image, caption=caption)
        new_post.save()
        return redirect('/')
    else:
        return redirect('/')


@login_required(login_url='signin')
def like_post(request):
    username = request.user.username
    post_id = request.GET.get('post_id')

    post = Post.objects.get(id=post_id)

    like_filter = LikePost.objects.filter(post_id=post_id, username=username).first()

    if like_filter is None:
        new_like = LikePost.objects.create(post_id=post_id, username=username)
        new_like.save()
        post.num_likes = post.num_likes + 1
        post.save()
        return redirect('/')
    else:
        like_filter.delete()
        post.num_likes = post.num_likes - 1
        post.save()
        return redirect('/')


def profile(request, pk):
    user_object = User.objects.get(username=pk)
    user_profile = Profile.objects.get(user=user_object)
    user_posts = Post.objects.filter(user=pk)
    quantity_posts = len(user_posts)

    follower = request.user.username
    user = pk
    followers_count_objects = FollowersCount.objects.all()

    if followers_count_objects.filter(follower=follower, user=user).first():
        button_text = "Unfollow"
    else:
        button_text = "Follow"

    user_followers = len(followers_count_objects.filter(user=pk))
    user_following = len(followers_count_objects.filter(follower=pk))
    context = {
        'title': f'Profile {pk}',
        'user_object': user_object,
        'user_profile': user_profile,
        'user_posts': user_posts,
        'quantity_posts': quantity_posts,
        'button_text': button_text,
        'user_following': user_following,
        'user_followers': user_followers,
    }
    return render(request, 'profile.html', context)


@login_required(login_url='signin')
def follow(request):
    if request.method == 'POST':
        follower = request.POST['follower']
        user = request.POST['user']

        if FollowersCount.objects.filter(follower=follower, user=user).first():
            delete_follower = FollowersCount.objects.get(follower=follower, user=user)
            delete_follower.delete()
            return redirect(f'/profile/{user}')
        else:
            new_follower = FollowersCount.objects.create(follower=follower, user=user)
            new_follower.save()
            return redirect(f'/profile/{user}')
    else:
        return redirect('/')


def search(request):
    user_object = User.objects.get(username=request.user.username)
    user_profile = Profile.objects.get(user=user_object)
    context = {
        'user_object': user_object,
        'user_profile': user_profile,
        'title': 'Search '
    }

    if request.method == 'POST':
        username = request.POST['username']
        print('+++++++++++', username)
        username_object = User.objects.filter(username__icontains=username)

        username_profile = []
        username_profile_list = []

        for users in username_object:
            username_profile.append(users.id)
        for ids in username_profile:
            profile_lists = Profile.objects.filter(id_user=ids)
            username_profile_list.append(profile_lists)
        username_profile_list = list(chain(*username_profile_list))

        context['username_profile_list'] = username_profile_list
    return render(request, 'search.html', context)
