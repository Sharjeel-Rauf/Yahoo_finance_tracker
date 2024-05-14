from django.shortcuts import render, redirect

from django.contrib.auth import login, logout

from .forms import SignUpForm

# Create your views here.

# view of the landing page
def front_page_view(request):
    context = {}
    context['page_title'] = 'Comprehensive Options Strategy Analyzer'
    return render(request, 'finance_app/frontpage.html', context)


# logout view
def LogoutView(request):
    logout(request)
    return redirect('frontpage')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            return redirect('frontpage')
    else:
        form = SignUpForm()
    
    return render(request, 'finance_app/signup.html', {'form': form})