from django.shortcuts import render

def tutorial(request):
    context = {}
    return render(request, 'tutorial.html', context)


def rnd(request):
    context = {}
    return render(request, 'rnd.html', context)
