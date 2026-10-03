from django.shortcuts import render, redirect
from .models import Request

def index(request):
    template_data = {}
    template_data['title'] = 'Suggest an improvement'
    template_data['categories'] = Request.CATEGORIES
    if request.method == 'POST' and request.user.is_authenticated:
        message = request.POST.get('message', '').strip()
        category = request.POST.get('category', '')
        if category not in dict(Request.CATEGORIES):
            category = 'other'
        if message:
            Request.objects.create(user=request.user, category=category, message=message[:1000])
            return redirect('/feedback/?sent=1')
        template_data['error'] = 'Please write a message before sending.'
    if request.user.is_authenticated:
        template_data['my_requests'] = Request.objects.filter(user=request.user).order_by('-date')
    return render(request, 'feedback/index.html', {'template_data': template_data})
