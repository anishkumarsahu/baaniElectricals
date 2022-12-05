import calendar
import os
from datetime import datetime, timedelta
from functools import wraps
import csv
# import xlwt
from activation.models import *
from activation.views import is_activated
from dateutil.relativedelta import relativedelta
from django.contrib.auth import logout, authenticate, login
from django.db.models import Max, Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
# Create your views here.
from django.views.decorators.csrf import csrf_exempt


# def login_or_logout(request, type):
#     try:
#         data = LoginAndLogoutStatus()
#         data.statusType = type
#         if request.user.username != 'anish':
#             staff = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
#             data.userID_id = staff.pk
#             data.save()
#     except:
#         pass


def check_group(group_name):
    def _check_group(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.groups.filter(name=group_name).exists():
                return redirect('/')
            return view_func(request, *args, **kwargs)

        return wrapper

    return _check_group

def check_two_group(admin, collector):
    def _check_group(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.user.groups.filter(name=admin).exists() or request.user.groups.filter(name=collector).exists():
                pass
            else:
                return redirect('/')
            return view_func(request, *args, **kwargs)

        return wrapper

    return _check_group


def loginPage(request):
    # if not request.user.is_authenticated:
    return render(request, 'home/login.html')
    # else:
    #     return redirect('/admin_home/')


@check_two_group('Admin','Moderator')
def admin_home(request):
    try:
        val = Validity.objects.last()
        message = "Your App License is Valid till {}".format(val.expiryDate.strftime('%d-%m-%Y'))
    except:
        message = "You are using a trial version."

    context = {
        'message': message,
    }
    return render(request, 'home/admin/index.html', context)

@check_group('Collection')
def collection_home(request):
    return render(request, 'home/collection/indexCollection.html')


@check_two_group('Admin','Moderator')
@is_activated()
def user_list(request):
    groups = StaffGroup.objects.filter(isDeleted__exact=False).order_by('name')
    party_groups = PartyGroup.objects.filter(isDeleted__exact=False).order_by('name')
    context = {
        'groups': groups,
        'party_groups': party_groups
    }
    return render(request, 'home/admin/userList.html', context)



@check_two_group('Admin','Moderator')
@is_activated()
def party_group_list(request):
    return render(request, 'home/admin/partyGroupList.html')


@check_two_group('Admin','Moderator')
@is_activated()
def bank_list(request):
    return render(request, 'home/admin/BankList.html')


@check_two_group('Admin','Moderator')
@is_activated()
def party_list(request):
    party_groups = PartyGroup.objects.filter(isDeleted__exact=False).order_by('name')
    staffs = StaffUser.objects.filter(isDeleted__exact=False).order_by('name')
    context = {
        'party_groups': party_groups,
        'staffs': staffs
    }
    return render(request, 'home/admin/PartyList.html', context)


def user_logout(request):
    # login_or_logout(request, 'Logout')
    logout(request)
    return redirect("homeApp:loginPage")


def my_profile(request):
    instance = get_object_or_404(StaffUser, user_ID_id=request.user.pk)
    context = {
        'instance': instance
    }
    return render(request, 'home/admin/profileAdmin.html', context)


def my_profile_collection(request):
    instance = get_object_or_404(StaffUser, user_ID_id=request.user.pk)
    context = {
        'instance': instance
    }
    return render(request, 'home/collection/profile.html', context)


@csrf_exempt
def postLogin(request):
    if request.method == 'POST':
        username = request.POST.get('userName')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            # login_or_logout(request, 'Login')
            if 'Admin' in request.user.groups.values_list('name', flat=True) or 'Moderator' in request.user.groups.values_list('name', flat=True) :
                return JsonResponse({'message': 'success', 'data': '/home/'}, safe=False)
            elif 'Collection' in request.user.groups.values_list('name', flat=True):
                return JsonResponse({'message': 'success', 'data': '/home/'}, safe=False)
        else:
            return JsonResponse({'message': 'fail'}, safe=False)

        # else:
        #     return JsonResponse({'message': 'fail'}, safe=False)
    else:
        return JsonResponse({'message': 'fail'}, safe=False)


#
def homepage(request):
    if request.user.is_authenticated:
        if 'Admin' in request.user.groups.values_list('name', flat=True) or 'Moderator' in request.user.groups.values_list('name', flat=True):
            return redirect('/admin_home/')
        elif 'Collection' in request.user.groups.values_list('name', flat=True):
            return redirect('/collection_home/')
        else:

            return render(request, 'home/login.html')


def add_collection(request):
    instance = Bank.objects.filter(isDeleted__exact=False).order_by('name')
    staffs = StaffUser.objects.filter(isDeleted__exact=False, group__iexact='Collection').order_by('name')
    p_groups = PartyGroup.objects.filter(isDeleted__exact=False).order_by('name')
    context = {
        'instance': instance,
        'staffs': staffs,
        'p_groups': p_groups,
    }
    return render(request, 'home/collection/addCollection.html', context)


def my_collection(request):
    context = {
    }
    return render(request, 'home/collection/collectionListByStaff.html', context)


# admin
@is_activated()
@check_two_group('Admin','Moderator')
def collection_list(request):
    staffs = StaffUser.objects.filter(isDeleted__exact=False).order_by('name')
    context = {
        'staffs': staffs
    }
    return render(request, 'home/admin/collectionListByAdmin.html', context)

@check_two_group('Admin','Moderator')
def take_collection(request):
    instance = Bank.objects.filter(isDeleted__exact=False).order_by('name')
    context = {
        'instance': instance
    }
    return render(request, 'home/admin/takeCollection.html', context)


def edit_collection(request, id = None):
    obj = get_object_or_404(Collection, pk = id)
    instance = Bank.objects.filter(isDeleted__exact=False).order_by('name')
    context = {
        'instance': instance,
        'obj':obj
    }
    return render(request, 'home/admin/editCollection.html', context)


def get_party_data(request):
    module_dir = os.path.dirname(__file__)  # get current directory
    file_path = os.path.join(module_dir, 'PartiesCSV.csv')
    with open(file_path, mode='r') as file:
        # reading the CSV file
        csvFile = csv.reader(file)
        # displaying the contents of the CSV file
        for lines in csvFile:
            try:
                partyGroup = PartyGroup.objects.get(name__iexact=lines[2])
                party = partyGroup.pk
            except:
                party = None

            try:
                user = StaffUser.objects.get(name__iexact=lines[3])
                usr = user.pk
            except:
                usr = None
            p = Party()
            p.name = lines[0]
            p.phone = lines[1]
            p.partyGroupID_id = party
            p.assignTo_id = usr
            p.save()
    return HttpResponse('Ok')


def generate_collection_date(request):
    col = Collection.objects.all()
    for c in col:
        c.collectionDateTime = c.datetime
        c.save()
    return HttpResponse('Ok')