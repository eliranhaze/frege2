from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def index(request):
    return HttpResponse("Hello, universe!!! You're at the polls index.")

def detail(request, qid):
    return HttpResponse("You're looking at the results of question %s." % qid) 

def vote(request, qid):
    return HttpResponse("You're voting on question %s." % qid) 
