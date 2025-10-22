from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def index(request):
    return render(request, 'index.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')

        print("DEBUG:", username, email, password, confirm)  # Check terminal

        if password != confirm:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            messages.success(request, "User created successfully!")
            return redirect('login')
    return render(request, 'Register.html')


from django.contrib.auth.models import User

def login_view(request):
    if request.method == 'POST':
        login_input = request.POST.get('username')
        password = request.POST.get('password')

        # Check if input is an email
        try:
            user_obj = User.objects.get(email=login_input)
            username = user_obj.username
        except User.DoesNotExist:
            username = login_input

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials.')
    return render(request, 'Login.html')


@login_required
def dashboard_view(request):
    return render(request, 'Dashboard.html', {'user': request.user})

def logout_view(request):
    logout(request)
    return redirect('login')
