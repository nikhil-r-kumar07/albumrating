from django.shortcuts import render
from .forms import CustomUserCreationForm, CustomErrorList
from django.contrib.auth import login as auth_login, authenticate, logout as auth_logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages

@login_required
def delete_account(request):
    template_data = {}
    template_data['title'] = 'Delete Account'
    if request.method == 'POST':
        if request.user.check_password(request.POST.get('password', '')):
            user = request.user
            auth_logout(request)
            user.delete()
            return redirect('home.index')
        template_data['error'] = 'That password is incorrect.'
    return render(request, 'accounts/delete_account.html', {'template_data': template_data})

@login_required
def logout(request):
    auth_logout(request)
    return redirect('home.index')
def signup(request):
    template_data = {}
    template_data['title'] = 'Sign Up'
    if request.method == 'GET':
        template_data['form'] = CustomUserCreationForm()
        return render(request, 'accounts/signup.html', {'template_data': template_data})
    elif request.method == 'POST':
        form = CustomUserCreationForm(request.POST, error_class=CustomErrorList)
        if form.is_valid():
            form.save()
            return redirect('accounts.login')
        else:
            template_data['form'] = form
            return render(request, 'accounts/signup.html', {'template_data': template_data})
def login(request):
    template_data = {}
    template_data['title'] = 'Login'
    if request.method == 'GET':
        return render(request, 'accounts/login.html', {'template_data': template_data})
    elif request.method == 'POST':
        user = authenticate(
            request,
            username = request.POST['username'],
            password = request.POST['password']
        )
        if user is None:
            template_data['error'] = 'The username or password is incorrect.'
            return render(request, 'accounts/login.html', {'template_data': template_data})
        else:
            auth_login(request, user)
            return redirect('home.index')
@login_required
def change_password(request):
    template_data = {}
    template_data['title'] = 'Change password'
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST, error_class=CustomErrorList)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)  # stay logged in after the change
            messages.success(request, 'Your password was changed.')
            return redirect('profiles.edit')
    else:
        form = PasswordChangeForm(request.user)
    template_data['form'] = form
    return render(request, 'accounts/change_password.html', {'template_data': template_data})
