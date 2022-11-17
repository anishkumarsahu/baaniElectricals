import requests

from django.contrib.auth import authenticate, login
from django.db import transaction
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta
from home.models import *
from django_datatables_view.base_datatable_view import BaseDatatableView
from django.utils.html import escape
from django.core.cache import cache


def deduct_location_balance(lat, lng):
    location = GeolocationPackage.objects.filter(isDeleted__exact=False).last()
    if location.used < location.balance:

        r = requests.get(
            "https://revgeocode.search.hereapi.com/v1/revgeocode?at=" + lat + "%2C" + lng + "&lang=en-US&apikey=VtAAEVuyqdswCZr8X1BdBzM-4JTpeAdivmp4_3ILPs4")
        data = r.json()
        location.used = (location.used + 1)
        location.save()
        return data["items"][0]["address"]["label"]
    else:
        return ""


#
@transaction.atomic
@csrf_exempt
def add_staff_api(request):
    if request.method == 'POST':
        try:
            CompanyUserName = request.POST.get("CompanyUserName")
            UserPhoneNo = request.POST.get("UserPhoneNo")
            UserEmail = request.POST.get("UserEmail")
            UserAddress = request.POST.get("UserAddress")
            UserGroup = request.POST.get("UserGroup")
            UserStatus = request.POST.get("UserStatus")
            UserPwd = request.POST.get("UserPwd")
            PartyGroup = request.POST.get("PartyGroup")
            imageUpload = request.FILES["imageUpload"]
            imageUploadID = request.FILES["imageUploadID"]

            staff = StaffUser()
            staff.photo = imageUpload
            staff.idProof = imageUploadID
            staff.name = CompanyUserName
            staff.phone = UserPhoneNo
            staff.email = UserEmail
            staff.address = UserAddress
            staff.group = UserGroup
            staff.isActive = UserStatus
            staff.userPassword = UserPwd
            staff.partyGroupID_id = int(PartyGroup)
            staff.save()
            username = 'USER' + get_random_string(length=3, allowed_chars='1234567890')
            while User.objects.select_related().filter(username__exact=username).count() > 0:
                username = 'USER' + get_random_string(length=5, allowed_chars='1234567890')
            else:
                new_user = User()
                new_user.username = username
                new_user.set_password(UserPwd)

                new_user.save()
                staff.username = username
                staff.user_ID_id = new_user.pk

                staff.save()

                try:
                    g = Group.objects.get(name=UserGroup)
                    g.user_set.add(new_user.pk)
                    g.save()

                except:
                    g = Group()
                    g.name = UserGroup
                    g.save()
                    g.user_set.add(new_user.pk)
                    g.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


#
class StaffUserListJson(BaseDatatableView):
    order_columns = ['photo', 'name', 'username', 'userPassword', 'group', 'partyGroupID.name', 'phone', 'address',
                     'isActive', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return StaffUser.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(username__icontains=search) | Q(partyGroupID__name__icontains=search)
                | Q(group__icontains=search) | Q(phone__icontains=search)
                | Q(address__icontains=search) | Q(isActive__icontains=search)
                | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            images = '<img class="ui avatar image" src="{}">'.format(item.photo.thumbnail.url)

            action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            json_data.append([
                images,  # escape HTML for security reasons
                escape(item.name),
                escape(item.username),
                escape(item.userPassword),
                escape(item.group),
                escape(item.partyGroupID.name),
                escape(item.phone),
                escape(item.address),
                escape(item.isActive),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@transaction.atomic
@csrf_exempt
def delete_staff_user(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            staff = StaffUser.objects.select_related().get(pk=int(id))
            staff.isDeleted = True
            staff.save()
            new_user = User.objects.select_related().get(pk=staff.user_ID_id)
            new_user.is_active = False
            new_user.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


def get_staff_user_detail(request):
    id = request.GET.get('id')
    C_User = get_object_or_404(StaffUser, id=id)
    # instance = BankDetails.objects.get(companyID_id=company.pk)

    data = {
        'ID': C_User.pk,
        'UserName': C_User.name,
        'UserPhone': C_User.phone,
        'UserAddress': C_User.address,
        'UserEmail': C_User.email,
        'UserPassword': C_User.userPassword,
        'UserGroup': C_User.group,
        'PartyGroup': C_User.partyGroupID.id,
        'IsActive': C_User.isActive,
        'ImgUrl': C_User.photo.medium.url,
        'IDUrl': C_User.idProof.medium.url

    }
    return JsonResponse({'data': data}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_staff_api(request):
    if request.method == 'POST':
        try:
            EditUserId = request.POST.get("EditUserId")
            CompanyUserName = request.POST.get("CompanyUserName")
            UserPhoneNo = request.POST.get("UserPhoneNo")
            UserEmail = request.POST.get("UserEmail")
            UserAddress = request.POST.get("UserAddress")
            UserGroup = request.POST.get("UserGroup")
            UserStatus = request.POST.get("UserStatus")
            UserPwd = request.POST.get("UserPwd")
            PartyGroup = request.POST.get("PartyGroup")

            staff = StaffUser.objects.select_related().get(pk=int(EditUserId))
            try:
                imageUpload = request.FILES["imageUpload"]
                staff.photo = imageUpload
            except:
                pass
            try:
                imageUploadID = request.FILES["imageUploadID"]
                staff.idProof = imageUploadID
            except:
                pass
            staff.name = CompanyUserName
            staff.phone = UserPhoneNo
            staff.email = UserEmail
            staff.address = UserAddress
            staff.group = UserGroup
            staff.partyGroupID_id = PartyGroup
            staff.isActive = UserStatus
            staff.userPassword = UserPwd
            staff.save()

            new_user = User.objects.select_related().get(pk=staff.user_ID_id)
            new_user.set_password(UserPwd)
            if UserStatus == 'Active':
                new_user.is_active = True
            else:
                new_user.is_active = False
            new_user.save()
            new_user.groups.clear()
            try:
                g = Group.objects.get(name=UserGroup)
                g.user_set.add(new_user.pk)
                g.save()

            except:
                g = Group()
                g.name = UserGroup
                g.save()
                g.user_set.add(new_user.pk)
                g.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


#
# # ---------------------------------Party Groups ----------------------------------------------------
#
@transaction.atomic
@csrf_exempt
def add_party_group_api(request):
    if request.method == 'POST':
        try:
            groupName = request.POST.get("groupName")
            description = request.POST.get("description")

            obj = PartyGroup()
            obj.name = groupName
            obj.description = description
            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


#
@transaction.atomic
@csrf_exempt
def delete_part_group(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            obj = PartyGroup.objects.select_related().get(pk=int(id))
            obj.isDeleted = True
            obj.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class PartyGroupListJson(BaseDatatableView):
    order_columns = ['name', 'description', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return PartyGroup.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
                | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            action = '''<button  data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button  data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            json_data.append([
                escape(item.name),
                escape(item.description),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


def get_party_group_detail(request):
    id = request.GET.get('id')
    instance = get_object_or_404(PartyGroup, id=id)
    # instance = BankDetails.objects.get(companyID_id=company.pk)

    data = {
        'ID': instance.pk,
        'Name': instance.name,
        'Description': instance.description,
    }
    return JsonResponse({'data': data}, safe=False)


#
@transaction.atomic
@csrf_exempt
def edit_part_group_api(request):
    if request.method == 'POST':
        try:
            Id = request.POST.get("EditId")
            name = request.POST.get("groupName")
            description = request.POST.get("description")
            obj = PartyGroup.objects.select_related().get(id=int(Id))
            obj.name = name
            obj.description = description

            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


# # ----------------------------------Banks------------------------
@transaction.atomic
@csrf_exempt
def add_bank_api(request):
    if request.method == 'POST':
        try:
            bankName = request.POST.get("bankName")
            accountNumber = request.POST.get("accountNumber")
            description = request.POST.get("description")

            obj = Bank()
            obj.name = bankName
            obj.accountNumber = accountNumber
            obj.description = description
            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class BankListJson(BaseDatatableView):
    order_columns = ['name', 'accountNumber', 'description', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Bank.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(accountNumber__icontains=search) | Q(description__icontains=search)
                | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            action = '''<button  data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button  data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            json_data.append([
                escape(item.name),
                escape(item.accountNumber),
                escape(item.description),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


def get_bank_detail(request):
    id = request.GET.get('id')
    instance = get_object_or_404(Bank, id=id)
    # instance = BankDetails.objects.get(companyID_id=company.pk)

    data = {
        'ID': instance.pk,
        'Name': instance.name,
        'AccountNumber': instance.accountNumber,
        'Description': instance.description,
    }
    return JsonResponse({'data': data}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_bank_api(request):
    if request.method == 'POST':
        try:
            Id = request.POST.get("EditId")
            name = request.POST.get("bankName")
            accountNumber = request.POST.get("accountNumber")
            description = request.POST.get("description")
            obj = Bank.objects.select_related().get(id=int(Id))
            obj.name = name
            obj.accountNumber = accountNumber
            obj.description = description

            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def delete_bank(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            obj = Bank.objects.select_related().get(pk=int(id))
            obj.isDeleted = True
            obj.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


# ----------------------------- Party ---------------------
@transaction.atomic
@csrf_exempt
def add_party_api(request):
    if request.method == 'POST':
        try:
            partyName = request.POST.get("partyName")
            phoneNumber = request.POST.get("phoneNumber")
            partyGroup = request.POST.get("partyGroup")
            address = request.POST.get("address")

            obj = Party()
            obj.name = partyName
            obj.phone = phoneNumber
            obj.address = address
            obj.partyGroupID_id = int(partyGroup)
            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class PartyListJson(BaseDatatableView):
    order_columns = ['name', 'phone', 'partyGroupID.name', 'address', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Party.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(phone__icontains=search) | Q(address__icontains=search)
                | Q(partyGroupID__name__icontains=search) | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            action = '''<button  data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button  data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            json_data.append([
                escape(item.name),
                escape(item.phone),
                escape(item.partyGroupID.name),
                escape(item.address),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


def get_party_detail(request):
    id = request.GET.get('id')
    instance = get_object_or_404(Party, id=id)
    # instance = BankDetails.objects.get(companyID_id=company.pk)

    data = {
        'ID': instance.pk,
        'Name': instance.name,
        'PhoneNumber': instance.phone,
        'Address': instance.address,
        'PartyGroup': instance.partyGroupID.id,
    }
    return JsonResponse({'data': data}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_party_api(request):
    if request.method == 'POST':
        try:
            Id = request.POST.get("EditId")
            name = request.POST.get("partyName")
            phoneNumber = request.POST.get("phoneNumber")
            address = request.POST.get("address")
            partyGroup = request.POST.get("partyGroup")
            obj = Party.objects.select_related().get(id=int(Id))
            obj.name = name
            obj.phone = phoneNumber
            obj.address = address
            obj.partyGroupID_id = int(partyGroup)

            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def delete_party(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            obj = Party.objects.select_related().get(pk=int(id))
            obj.isDeleted = True
            obj.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


def list_party_api(request):
    try:
        o_list = []
        if cache.get('PartyList'):
            o_list = cache.get('PartyList')

        else:
            obj_list = Party.objects.select_related().filter(isDeleted__exact=False).order_by(
                'name')

            for obj in obj_list:
                obj_dic = {
                    'ID': obj.pk,
                    'Name': obj.name,
                    'Address': obj.address,
                    'Phone': obj.phone,
                    'Detail': obj.name + ' - ' + obj.address + ' @ ' + str(obj.pk),
                    'DisplayDetail': obj.name + ' - ' + obj.address
                }
                o_list.append(obj_dic)
            cache.set('PartyList', o_list, timeout=None)

        return JsonResponse({'message': 'success', 'data': o_list}, safe=False)
    except:
        return JsonResponse({'message': 'error'}, safe=False)


# ------------------------------Collection ----------------------------------------
# ----------------------------- Party ---------------------
@transaction.atomic
@csrf_exempt
def add_collection_by_staff_api(request):
    if request.method == 'POST':
        try:
            party = request.POST.get("party")
            paymentMode = request.POST.get("paymentMode")
            amountPaid = request.POST.get("amountPaid")
            bank = request.POST.get("bank")
            detail = request.POST.get("detail")
            remark = request.POST.get("remark")
            lat = request.POST.get("lat")
            lng = request.POST.get("lng")
            c = str(party).split('@')
            cus = Party.objects.select_related().get(pk=int(c[1]))
            obj = Collection()
            obj.partyID_id = cus.pk
            obj.modeOfPayment = paymentMode
            obj.paidAmount = float(amountPaid)
            try:
                obj.bankID_id = int(bank)
            except:
                pass
            obj.detail = detail
            obj.remark = remark
            obj.latitude = lat
            obj.longitude = lng
            user = StaffUser.objects.get(user_ID_id=request.user.pk)
            obj.collectedBy_id = user.pk
            try:
                obj.collectionAddress = deduct_location_balance(lat, lng)
                # r = requests.get(
                #     "https://revgeocode.search.hereapi.com/v1/revgeocode?at=" + lat + "%2C" + lng + "&lang=en-US&apikey=VtAAEVuyqdswCZr8X1BdBzM-4JTpeAdivmp4_3ILPs4")
                # data = r.json()
                # obj.collectionAddress = data["items"][0]["address"]["label"]
            except:
                pass

            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def add_collection_by_admin_api(request):
    if request.method == 'POST':
        try:
            party = request.POST.get("party")
            paymentMode = request.POST.get("paymentMode")
            amountPaid = request.POST.get("amountPaid")
            bank = request.POST.get("bank")
            detail = request.POST.get("detail")
            remark = request.POST.get("remark")
            lat = request.POST.get("lat")
            lng = request.POST.get("lng")
            c = str(party).split('@')
            cus = Party.objects.select_related().get(pk=int(c[1]))
            obj = Collection()
            obj.partyID_id = cus.pk
            obj.modeOfPayment = paymentMode
            obj.paidAmount = float(amountPaid)
            try:
                obj.bankID_id = int(bank)
            except:
                pass
            obj.detail = detail
            obj.remark = remark
            obj.latitude = lat
            obj.longitude = lng
            user = StaffUser.objects.get(user_ID_id=request.user.pk)
            obj.collectedBy_id = user.pk
            obj.isApproved = True
            obj.approvedBy_id = user.pk
            obj.collectionAddress = "From Shop."

            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class CollectionByStaffListJson(BaseDatatableView):
    order_columns = ['partyID.name', 'paidAmount', 'modeOfPayment', 'bankID.name', 'detail', 'remark',
                     'collectionAddress', 'datetime']

    def get_initial_queryset(self):
        # user = StaffUser.objects.get(user_ID__id = self.request.pk)
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Collection.objects.select_related().filter(isDeleted__exact=False,
                                                          datetime__icontains=datetime.today().date(),
                                                          collectedBy__user_ID_id=self.request.user.pk)

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(partyID__name__icontains=search) | Q(paidAmount__icontains=search) | Q(
                    modeOfPayment__icontains=search)
                | Q(bankID__name__icontains=search) | Q(detail__icontains=search) | Q(detail__icontains=search) | Q(
                    remark__icontains=search)
                | Q(datetime__icontains=search) | Q(collectionAddress__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            # action = '''<button  data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
            #         <i class="pen icon"></i>
            #       </button>
            #       <button  data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
            #         <i class="trash alternate icon"></i>
            #       </button>'''.format(item.pk, item.pk),
            action = '''<div class="ui tiny label">
  Denied
</div>''',
            try:
                bank = item.bankID.name
            except:
                bank = '-'
            json_data.append([
                escape(item.partyID.name),
                escape(item.paidAmount),
                escape(item.modeOfPayment),
                escape(bank),
                escape(item.detail),
                escape(item.remark),
                escape(item.collectionAddress),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


class CollectionByAdminListJson(BaseDatatableView):
    order_columns = ['partyID.name', 'paidAmount', 'modeOfPayment', 'bankID.name', 'detail', 'remark',
                     'collectionAddress', 'collectedBy.name', 'datetime', 'isApproved', 'approvedBy.ane']

    def get_initial_queryset(self):
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')
            return Collection.objects.select_related().filter(isDeleted__exact=False, datetime__range=(
            sDate.date(), eDate.date() + timedelta(days=1)))
        except:
            return Collection.objects.select_related().filter(isDeleted__exact=False,
                                                              datetime__icontains=datetime.today().date())

    def filter_queryset(self, qs):
        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(partyID__name__icontains=search) | Q(paidAmount__icontains=search) | Q(
                    modeOfPayment__icontains=search)
                | Q(bankID__name__icontains=search) | Q(detail__icontains=search) | Q(detail__icontains=search) | Q(
                    remark__icontains=search)
                | Q(datetime__icontains=search) | Q(collectionAddress__icontains=search) | Q(
                    collectedBy__name__icontains=search)
                | Q(approvedBy__name__icontains=search) | Q(isApproved__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            action = '''<button  data-inverted="" data-tooltip="Make Approval" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick = "showConfirmationModal('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button  data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button>'''.format(item.pk, item.pk),

            try:
                bank = item.bankID.name
            except:
                bank = '-'
            try:
                collectedBy = item.collectedBy.name
            except:
                collectedBy = '-'
            try:
                approvedBy = item.approvedBy.name
            except:
                approvedBy = '-'
            if item.isApproved == True:
                isApproved = '''<div class="ui tiny green label">
                  Yes
                </div>'''
            else:
                isApproved = '''<div class="ui tiny red label">
                  No
                </div>'''

            json_data.append([
                escape(item.partyID.name),
                escape(item.paidAmount),
                escape(item.modeOfPayment),
                escape(bank),
                escape(item.detail),
                escape(item.remark),
                escape(item.collectionAddress),
                collectedBy,
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                isApproved,
                approvedBy,
                action,

            ])

        return json_data


@transaction.atomic
@csrf_exempt
def delete_collection(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            obj = Collection.objects.select_related().get(pk=int(id))
            obj.isDeleted = True
            obj.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def approve_collection(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            obj = Collection.objects.select_related().get(pk=int(id))
            user = StaffUser.objects.get(user_ID__id=request.user.pk)
            obj.isApproved = True
            obj.approvedBy_id = user.pk
            obj.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
def change_password_api(request):
    if request.method == 'POST':
        try:
            password = request.POST.get('password')
            data = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            data.userPassword = password
            data.save()
            user = User.objects.select_related().get(pk=request.user.pk)
            user.set_password(password)
            user.save()
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'message': 'success'}, safe=False)

            return JsonResponse({'message': 'success'}, safe=False)

        except:
            return JsonResponse({'message': 'error'}, safe=False)


def get_admin_dashboard_report_api(request):
    party = Party.objects.select_related().filter(isDeleted__exact=False)
    staff = StaffUser.objects.select_related().filter(isDeleted__exact=False)
    location = GeolocationPackage.objects.filter(isDeleted__exact=False).last()
    collection = Collection.objects.select_related().filter(isDeleted__exact=False,
                                                            datetime__icontains=datetime.today().date(),
                                                            )

    c_total = 0.0
    for c in collection:
        c_total = c_total + c.paidAmount

    data = {
        'partyCount': party.count(),
        'staffCount': staff.count(),
        'locationCount': str(int(location.used)) + '/' + str(int(location.balance)),
        'collection': c_total
    }
    return JsonResponse({'data': data}, safe=False)


def get_staff_dashboard_report_api(request):
    user = StaffUser.objects.get(user_ID__id=request.user.pk)
    party = Party.objects.select_related().filter(isDeleted__exact=False, partyGroupID__id=user.partyGroupID_id)
    collection_total = Collection.objects.select_related().filter(isDeleted__exact=False,
                                                                  collectedBy__user_ID_id=request.user.pk)
    collection = Collection.objects.select_related().filter(isDeleted__exact=False,
                                                            datetime__icontains=datetime.today().date(),
                                                            collectedBy__user_ID_id=request.user.pk
                                                            )

    c_total = 0.0
    for c in collection_total:
        c_total = c_total + c.paidAmount

    d_total = 0.0
    for d in collection:
        d_total = d_total + d.paidAmount

    data = {
        'partyCount': party.count(),
        'collection_totalCount': collection.count(),
        'collection_total': c_total,
        'collection': d_total
    }
    return JsonResponse({'data': data}, safe=False)
