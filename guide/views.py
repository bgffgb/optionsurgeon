from django.shortcuts import render

def tutorial(request):
    # Always render the same page
    context = {}
    return render(request, 'tutorial.html', context)


def rnd(request):
    # Always render the same page
    context = {}
    return render(request, 'rnd.html', context)
