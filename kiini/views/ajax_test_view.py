# kiini/views/ajax_test_view.py
from django.shortcuts import render

def ajax_test_page(request):
    return render(request, 'kiini/ajax_test.html')