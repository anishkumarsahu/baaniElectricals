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
            imageUpload = request.FILES["imageUpload"]

            staff = StaffUser()
            staff.photo = imageUpload
            staff.name = CompanyUserName
            staff.phone = UserPhoneNo
            staff.email = UserEmail
            staff.address = UserAddress
            staff.group = UserGroup
            staff.isActive = UserStatus
            staff.userPassword = UserPwd
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
                    h = Group.objects.get(name='Both')
                    g.user_set.add(new_user.pk)
                    g.save()
                    if UserGroup != 'Collection':
                        h.user_set.add(new_user.pk)
                        h.save()

                except:
                    g = Group()
                    g.name = UserGroup
                    g.save()
                    g.user_set.add(new_user.pk)
                    g.save()
                    if UserGroup != 'Collection':
                        h = Group()
                        h.name = 'Both'
                        h.save()
                        h.user_set.add(new_user.pk)
                        h.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class StaffUserListJson(BaseDatatableView):
    order_columns = ['photo', 'name', 'username', 'userPassword', 'group', 'phone', 'address', 'isActive', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return StaffUser.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(username__icontains=search)
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
        'IsActive': C_User.isActive,
        'ImgUrl': C_User.photo.medium.url

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

            staff = StaffUser.objects.select_related().get(pk=int(EditUserId))
            staff.name = CompanyUserName
            staff.phone = UserPhoneNo
            staff.email = UserEmail
            staff.address = UserAddress
            staff.group = UserGroup
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
                h = Group.objects.get(name='Both')
                g.user_set.add(new_user.pk)
                g.save()
                if UserGroup != 'Collection':
                    h.user_set.add(new_user.pk)
                    h.save()

            except:
                g = Group()
                g.name = UserGroup
                g.save()
                g.user_set.add(new_user.pk)
                g.save()
                if UserGroup != 'Collection':
                    h = Group()
                    h.name = 'Both'
                    h.save()
                    h.user_set.add(new_user.pk)
                    h.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


# ---------------------------------Product ----------------------------------------------------

@transaction.atomic
@csrf_exempt
def add_product_api(request):
    if request.method == 'POST':
        try:
            productName = request.POST.get("productName")
            stock = request.POST.get("stock")
            unit = request.POST.get("unit")
            category = request.POST.get("category")
            brand = request.POST.get("brand")
            cp = request.POST.get("cp")
            mrp = request.POST.get("mrp")
            sp = request.POST.get("sp")

            pro = Product()
            pro.name = productName
            pro.unitID = unit
            pro.categoryID = category
            pro.brandID = brand
            pro.stock = float(stock)
            pro.cp = float(cp)
            pro.mrp = float(mrp)
            pro.sp = float(sp)
            pro.save()
            cache.delete('ProductListCache')
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class ProductListJson(BaseDatatableView):
    order_columns = ['name', 'stock', 'unitID', 'categoryID', 'brandID', 'cp', 'mrp', 'sp', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Product.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(stock__icontains=search)
                | Q(unitID__icontains=search) | Q(categoryID__icontains=search)
                | Q(brandID__icontains=search) | Q(cp__icontains=search) |
                Q(mrp__icontains=search) | Q(sp__icontains=search)
                | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            action = '''<button  data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button  data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            json_data.append([
                escape(item.name),
                escape(item.stock),
                escape(item.unitID),
                escape(item.categoryID),
                escape(item.brandID),
                escape(item.cp),
                escape(item.mrp),
                escape(item.sp),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@transaction.atomic
@csrf_exempt
def delete_product(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            pro = Product.objects.select_related().get(pk=int(id))
            pro.isDeleted = True
            pro.save()
            cache.delete('ProductListCache')
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


def get_product_detail(request):
    id = request.GET.get('id')
    instance = get_object_or_404(Product, id=id)
    # instance = BankDetails.objects.get(companyID_id=company.pk)

    data = {
        'ID': instance.pk,
        'ProductName': instance.name,
        'Stock': instance.stock,
        'Unit': instance.unitID,
        'Category': instance.categoryID,
        'Brand': instance.brandID,
        'CP': instance.cp,
        'MRP': instance.mrp,
        'SP': instance.sp
    }
    return JsonResponse({'data': data}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_product_api(request):
    if request.method == 'POST':
        try:
            Id = request.POST.get("EditUserId")
            productName = request.POST.get("productName")
            stock = request.POST.get("stock")
            unit = request.POST.get("unit")
            category = request.POST.get("category")
            brand = request.POST.get("brand")
            cp = request.POST.get("cp")
            mrp = request.POST.get("mrp")
            sp = request.POST.get("sp")

            pro = Product.objects.select_related().get(id=int(Id))
            pro.name = productName
            pro.unitID = unit
            pro.categoryID = category
            pro.brandID = brand
            pro.stock = float(stock)
            pro.cp = float(cp)
            pro.mrp = float(mrp)
            pro.sp = float(sp)
            pro.save()
            cache.delete('ProductListCache')
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


# ---------------------------------Supplier ----------------------------------------------------

@transaction.atomic
@csrf_exempt
def add_supplier_api(request):
    if request.method == 'POST':
        try:
            supplierName = request.POST.get("supplierName")
            phone = request.POST.get("phone")
            gst = request.POST.get("gst")
            address = request.POST.get("address")

            obj = Supplier()
            obj.name = supplierName
            obj.phone = phone
            obj.gst = gst
            obj.address = address
            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def delete_supplier(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            obj = Supplier.objects.select_related().get(pk=int(id))
            obj.isDeleted = True
            obj.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class SupplierListJson(BaseDatatableView):
    order_columns = ['name', 'phone', 'gst', 'address', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Supplier.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(phone__icontains=search)
                | Q(gst__icontains=search) | Q(addtress__icontains=search)
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
                escape(item.phone),
                escape(item.gst),
                escape(item.address),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


def get_supplier_detail(request):
    id = request.GET.get('id')
    instance = get_object_or_404(Supplier, id=id)
    # instance = BankDetails.objects.get(companyID_id=company.pk)

    data = {
        'ID': instance.pk,
        'Name': instance.name,
        'Phone': instance.phone,
        'GST': instance.gst,
        'Address': instance.address,

    }
    return JsonResponse({'data': data}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_supplier_api(request):
    if request.method == 'POST':
        try:
            Id = request.POST.get("EditUserId")
            supplierName = request.POST.get("supplierName")
            phone = request.POST.get("phone")
            gst = request.POST.get("gst")
            address = request.POST.get("address")

            obj = Supplier.objects.select_related().get(id=int(Id))
            obj.name = supplierName
            obj.phone = phone
            obj.gst = gst
            obj.address = address
            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


# ----------------------------------Purchase------------------------

@csrf_exempt
@transaction.atomic
def add_purchase_api(request):
    if request.method == 'POST':
        taxable = request.POST.get("taxable")
        totalGst = request.POST.get("totalGst")
        otherCharges = request.POST.get("otherCharges")
        roundOff = request.POST.get("roundOff")
        grandTotal = request.POST.get("grandTotal")
        supplierNameID = request.POST.get("supplierNameID")
        invoice = request.POST.get("invoice")
        idate = request.POST.get("idate")
        datas = request.POST.get("datas")
        pur = Purchase()
        s = str(supplierNameID).split('|')
        pur.supplierID_id = int(s[1])
        pur.supplierName = s[0]
        pur.taxableAmount = float(taxable)
        pur.gstAmount = float(totalGst)
        pur.otherCharges = float(otherCharges)
        pur.roundOff = float(roundOff)
        pur.grandTotal = float(grandTotal)
        pur.invoiceNumber = invoice
        pur.invoiceDate = datetime.strptime(idate, '%d/%m/%Y')
        pur.save()

        splited_receive_item = datas.split("@")
        for item in splited_receive_item[:-1]:
            item_details = item.split('|')
            p = PurchaseProduct()
            p.purchaseID_id = pur.pk
            p.productID_id = int(item_details[0])
            p.productName = item_details[1]
            p.quantity = float(item_details[2])
            p.rate = float(item_details[3])
            p.gst = float(item_details[4])
            p.net = float(item_details[5])
            p.total = float(item_details[6])
            pro = Product.objects.select_related().get(pk=int(int(item_details[0])))
            ori_stock = pro.stock
            pro.stock = (ori_stock + float(item_details[2]))
            pro.save()
            p.save()
        return JsonResponse({'message': 'success'}, safe=False)


class PurchaseListJson(BaseDatatableView):
    order_columns = ['supplierName', 'invoiceNumber', 'invoiceDate', 'taxableAmount', 'gstAmount', 'otherCharges',
                     'roundOff', 'grandTotal', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Purchase.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(supplierName__icontains=search) | Q(invoiceNumber__icontains=search)
                | Q(invoiceDate__icontains=search) | Q(grandTotal__icontains=search)
                | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            action = '''<button  data-inverted="" data-tooltip="View Detail" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick = "GetPurchaseDetail('{}')" class="ui circular facebook icon button green">
                    <i class="receipt icon"></i>
                  </button>
                  <button  data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),

            json_data.append([
                escape(item.supplierName),
                escape(item.invoiceNumber),
                escape(item.invoiceDate.strftime('%d-%m-%Y')),
                escape(item.taxableAmount),
                escape(item.gstAmount),
                escape(item.otherCharges),
                escape(item.roundOff),
                escape(item.grandTotal),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


def get_purchase_detail(request, id=None):
    instance = get_object_or_404(Purchase, pk=id)
    basic = {
        'Name': instance.supplierName,
        'Gst': instance.supplierID.gst,
        'Phone': instance.supplierID.phone,
        'Address': instance.supplierID.address,
    }
    items = PurchaseProduct.objects.select_related().filter(purchaseID_id=instance.pk)
    item_list = []
    for i in items:
        item_dic = {
            'ItemID': i.pk,
            'ItemProductName': i.productName,
            'ItemQuantity': i.quantity,
            'ItemRate': i.rate,
            'ItemGst': i.gst,
            'ItemnetRate': i.net,
            'ItemTotal': i.total,

        }
        item_list.append(item_dic)

    data = {
        'Basic': basic,
        'Items': item_list

    }
    return JsonResponse({'data': data}, safe=False)


@csrf_exempt
@transaction.atomic
def delete_purchase(request):
    if request.method == 'POST':
        id = request.POST.get("ID")
        sale = Purchase.objects.select_related().get(pk=int(id))
        sale.isDeleted = True
        sale.save()
        sales_products = PurchaseProduct.objects.select_related().filter(purchaseID_id=int(id))
        for pro in sales_products:
            product = Product.objects.select_related().get(pk=pro.productID_id)
            product.stock = product.stock - pro.quantity
            product.save()
        return JsonResponse({'message': 'success'}, safe=False)


# ---------------------------------customer------------------------------------
@transaction.atomic
@csrf_exempt
def delete_customer_api(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            cus = Customer.objects.select_related().get(pk=int(id))
            cus.isDeleted = True
            cus.save()

            obj = Sale.objects.select_related().filter(isDeleted__exact=False, customerID_id=cus.pk)
            for o in obj:
                o.isDeleted = True
                o.save()
                pro = Product.objects.select_related().get(pk=o.productID_id)
                pro.stock = (pro.stock + 1)
                pro.save()
                ins = Installment.objects.select_related().filter(saleID_id=o.pk)
                for i in ins:
                    i.isDeleted = True
                    i.save()
            cache.delete('CustomerList')
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def add_customer_api(request):
    if request.method == 'POST':
        try:
            name = request.POST.get("name")
            phone = request.POST.get("phone")
            district = request.POST.get("district")
            address = request.POST.get("address")
            lat = request.POST.get("lat")
            lng = request.POST.get("lng")
            landmark = request.POST.get("landmark")
            photo = request.FILES["photo"]
            idf = request.FILES["idf"]
            idb = request.FILES["idb"]

            obj = Customer()
            obj.latitude = lat
            obj.longitude = lng
            obj.name = name
            obj.phoneNumber = phone
            obj.district = district
            obj.address = address
            obj.landmark = landmark
            obj.photo = photo
            obj.idProofFront = idf
            obj.idProofBack = idb
            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            obj.addedBy_id = user.pk
            todayDate = datetime.today().date()
            code = todayDate.strftime("%y%b")
            totalCustomer = Customer.objects.select_related().filter(isDeleted=False, datetime__year=todayDate.year,
                                                                     datetime__month=todayDate.month)
            obj.customerCode = str(code).upper() + str(totalCustomer.count()).zfill(3)
            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_customer_api(request):
    if request.method == 'POST':
        try:
            name = request.POST.get("name")
            phone = request.POST.get("phone")
            district = request.POST.get("district")
            address = request.POST.get("address")
            lat = request.POST.get("lat")
            lng = request.POST.get("lng")
            landmark = request.POST.get("landmark")
            cusID = request.POST.get("cusID")
            obj = Customer.objects.select_related().get(pk=int(cusID))
            try:
                photo = request.FILES["photo"]
                obj.photo = photo
            except:
                pass
            try:

                idf = request.FILES["idf"]
                obj.idProofFront = idf
            except:
                pass
            try:
                idb = request.FILES["idb"]
                obj.idProofBack = idb
            except:
                pass

            obj.latitude = lat
            obj.longitude = lng
            obj.name = name
            obj.phoneNumber = phone
            obj.district = district
            obj.address = address
            obj.landmark = landmark

            obj.save()
            cache.delete('CustomerList')
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class CustomerListByUserJson(BaseDatatableView):
    order_columns = ['photo', 'name', 'customerCode', 'phoneNumber', 'district', 'address', 'landmark',
                     'idProofFront', 'idProofBack', 'datetime']

    def get_initial_queryset(self):
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')

            return Customer.objects.select_related().filter(isDeleted__exact=False,
                                                            addedBy__user_ID_id__exact=self.request.user.pk,
                                                            datetime__range=(
                                                            sDate.date(), eDate.date() + timedelta(days=1)))

        except:

            return Customer.objects.select_related().filter(isDeleted__exact=False,
                                                            addedBy__user_ID_id__exact=self.request.user.pk)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(customerCode__icontains=search) | Q(district__icontains=search) | Q(address__icontains=search)
                | Q(phoneNumber__icontains=search)
                | Q(datetime__icontains=search) | Q(landmark__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []

        for item in qs:
            photo = '''<img style="cursor:pointer" onclick="showImgModal('{}')" class="ui avatar image" src="{}">'''.format(
                item.photo.large.url, item.photo.thumbnail.url)
            idProofFront = '''<img style="cursor:pointer" onclick="showImgModal('{}')" class="ui avatar image" src="{}">'''.format(
                item.idProofFront.large.url, item.idProofFront.thumbnail.url)
            idProofBack = '''<img style="cursor:pointer" onclick="showImgModal('{}')" class="ui avatar image" src="{}">'''.format(
                item.idProofBack.large.url, item.idProofBack.thumbnail.url)
            action = '''<a data-inverted="" data-tooltip="Customer Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/customer_detail/{}/" class="ui circular facebook icon button green">
                        <i class="receipt icon"></i>
                      </a>
                     </td>'''.format(item.pk),
            json_data.append([
                photo,  # escape HTML for security reasons
                escape(item.name),
                escape(item.customerCode),
                escape(item.phoneNumber),
                escape(item.district),
                escape(item.address),
                escape(item.landmark),
                idProofFront,
                idProofBack,
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action
            ])
        return json_data


class CustomerListAdminJson(BaseDatatableView):
    order_columns = ['photo', 'name', 'customerCode', 'phoneNumber', 'district', 'address', 'landmark',
                     'idProofFront', 'idProofBack', 'datetime']

    def get_initial_queryset(self):
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')

            return Customer.objects.select_related().filter(isDeleted__exact=False,
                                                            datetime__range=(
                                                            sDate.date(), eDate.date() + timedelta(days=1)))

        except:

            return Customer.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(customerCode__icontains=search) | Q(district__icontains=search) | Q(address__icontains=search)
                | Q(landmark__icontains=search) | Q(phoneNumber__icontains=search)
                | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []

        for item in qs:
            photo = '''<img style="cursor:pointer" onclick="showImgModal('{}')" class="ui avatar image" src="{}">'''.format(
                item.photo.large.url, item.photo.thumbnail.url)
            idProofFront = '''<img style="cursor:pointer" onclick="showImgModal('{}')" class="ui avatar image" src="{}">'''.format(
                item.idProofFront.large.url, item.idProofFront.thumbnail.url)
            idProofBack = '''<img style="cursor:pointer" onclick="showImgModal('{}')" class="ui avatar image" src="{}">'''.format(
                item.idProofBack.large.url, item.idProofBack.thumbnail.url)

            if 'Admin' in self.request.user.groups.values_list('name', flat=True):
                action = '''<a data-inverted="" data-tooltip="Customer Edit" data-position="left center" data-variation="mini" style="font-size:10px;" href="/customer_edit_admin/{}/" class="ui circular facebook icon button purple">
                                <i class="pen icon"></i>
                              </a>
                              <a data-inverted="" data-tooltip="Customer Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/customer_detail_admin/{}/" class="ui circular facebook icon button green">
                                <i class="receipt icon"></i>
                              </a>
                             <button data-inverted="" data-tooltip="Delete Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button>'''.format(item.pk, item.pk, item.pk),
            else:
                action = '''<a data-inverted="" data-tooltip="Customer Edit" data-position="left center" data-variation="mini" style="font-size:10px;" href="/customer_edit_admin/{}/" class="ui circular facebook icon button purple">
                                                <i class="pen icon"></i>
                                              </a>
                                              <a data-inverted="" data-tooltip="Customer Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/customer_detail_admin/{}/" class="ui circular facebook icon button green">
                                                <i class="receipt icon"></i>
                                              </a>
                                            '''.format(item.pk, item.pk),

            json_data.append([
                photo,  # escape HTML for security reasons
                escape(item.name),
                escape(item.customerCode),
                escape(item.phoneNumber),
                escape(item.district),
                escape(item.address),
                escape(item.landmark),
                idProofFront,
                idProofBack,
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action
            ])
        return json_data


# customer and product API list
def list_customer_api(request):
    try:
        o_list = []
        if cache.get('CustomerList'):
            o_list = cache.get('CustomerList')

        else:
            obj_list = Customer.objects.select_related().filter(isDeleted__exact=False).select_related().order_by(
                'name')

            for obj in obj_list:
                obj_dic = {
                    'ID': obj.pk,
                    'Name': obj.name,
                    'District': obj.district,
                    'Address': obj.address,
                    'Phone': obj.phoneNumber,
                    'Detail': obj.name + ' - ' + obj.address + ' @ ' + str(obj.pk),
                    'DisplayDetail': obj.name + ' - ' + obj.address
                }
                o_list.append(obj_dic)
            cache.set('CustomerList', o_list, timeout=None)

        return JsonResponse({'message': 'success', 'data': o_list}, safe=False)
    except:
        return JsonResponse({'message': 'error'}, safe=False)


def list_product_api(request):
    try:
        o_list = []
        if cache.get('ProductListCache'):
            o_list = cache.get('ProductListCache')
        else:
            obj_list = Product.objects.select_related().filter(isDeleted__exact=False).select_related().order_by('name')

            for obj in obj_list:
                obj_dic = {
                    'ID': obj.pk,
                    'Name': obj.name,
                    'Category': obj.categoryID,
                    'NetTotal': obj.sp,
                    'Detail': obj.name + ' - ' + obj.categoryID + ' @' + str(obj.pk),
                    'DisplayDetail': obj.name + ' - ' + obj.categoryID + ' - ' + obj.brandID + ' (₹ {})'.format(obj.sp)
                }
                o_list.append(obj_dic)
            cache.set('ProductListCache', o_list, timeout=None)
        return JsonResponse({'message': 'success', 'data': o_list}, safe=False)
    except:
        return JsonResponse({'message': 'error'}, safe=False)


# -----------------------------------sales-----------------------------------------

@transaction.atomic
@csrf_exempt
def delete_sale_api(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            obj = Sale.objects.select_related().get(pk=int(id))
            obj.isDeleted = True
            obj.save()
            pro = Product.objects.select_related().get(pk=obj.productID_id)
            pro.stock = (pro.stock + 1)
            pro.save()
            ins = Installment.objects.select_related().filter(saleID_id=obj.pk)
            for i in ins:
                i.isDeleted = True
                i.save()
            cache.delete('SalesListCache')
            return JsonResponse({'message': 'success'}, safe=False)

        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def add_sales_api(request):
    if request.method == 'POST':
        try:
            photo = request.FILES["photo"]
            customer = request.POST.get("customer")
            product = request.POST.get("product")
            emi = request.POST.get("emi")
            advance = request.POST.get("advance")
            tenure = request.POST.get("tenure")
            totalAmount = request.POST.get("totalAmount")
            lat = request.POST.get("lat")
            lng = request.POST.get("lng")
            remark = request.POST.get("remark")
            idate = request.POST.get("idate")
            c = str(customer).split('@')
            cus = Customer.objects.select_related().get(pk=int(c[1]))
            p = str(product).split('@')
            pro = Product.objects.select_related().get(pk=int(p[1]))
            obj = Sale()
            obj.latitude = lat
            obj.longitude = lng
            obj.customerName = cus.name
            obj.customerID_id = cus.pk
            obj.productName = pro.name
            obj.productID_id = pro.pk
            obj.unit = pro.unitID
            obj.quantity = 1
            obj.rate = pro.sp
            obj.advancePaid = float(advance)
            obj.amountPaid = float(advance)
            obj.tenureInMonth = float(tenure)
            obj.emiAmount = float(emi)
            obj.totalAmount = float(totalAmount)
            obj.remark = remark
            obj.deliveryPhoto = photo
            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            obj.addedBy_id = user.pk
            obj.assignedTo_id = user.pk
            obj.installmentStartDate = datetime.strptime(idate, '%d/%m/%Y')
            obj.save()
            obj.saleNo = str(obj.pk).zfill(7)
            obj.save()
            pro.stock = pro.stock - 1
            pro.save()
            for i in range(0, int(tenure)):
                inst = Installment()
                inst.saleID_id = obj.pk
                inst.emiAmount = obj.emiAmount
                inst.assignedTo_id = user.pk
                inst.installmentDate = obj.installmentStartDate + relativedelta(months=+i)
                inst.save()
            cache.delete('SalesListCache')
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def add_sales_admin_api(request):
    if request.method == 'POST':
        try:
            photo = request.FILES["photo"]
            customer = request.POST.get("customer")
            product = request.POST.get("product")
            emi = request.POST.get("emi")
            advance = request.POST.get("advance")
            tenure = request.POST.get("tenure")
            totalAmount = request.POST.get("totalAmount")
            lat = request.POST.get("lat")
            lng = request.POST.get("lng")
            remark = request.POST.get("remark")
            idate = request.POST.get("idate")
            assignTo = request.POST.get("assignTo")
            c = str(customer).split('@')
            cus = Customer.objects.select_related().get(pk=int(c[1]))
            p = str(product).split('@')
            pro = Product.objects.select_related().get(pk=int(p[1]))
            obj = Sale()
            obj.latitude = lat
            obj.longitude = lng
            obj.customerName = cus.name
            obj.customerID_id = cus.pk
            obj.productName = pro.name
            obj.productID_id = pro.pk
            obj.unit = pro.unitID
            obj.quantity = 1
            obj.rate = pro.sp
            obj.advancePaid = float(advance)
            obj.amountPaid = float(advance)
            obj.tenureInMonth = float(tenure)
            obj.emiAmount = float(emi)
            obj.totalAmount = float(totalAmount)
            obj.remark = remark
            obj.deliveryPhoto = photo
            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            obj.addedBy_id = user.pk
            obj.assignedTo_id = int(assignTo)
            obj.installmentStartDate = datetime.strptime(idate, '%d/%m/%Y')
            obj.save()
            obj.saleNo = str(obj.pk).zfill(7)
            obj.save()
            pro.stock = pro.stock - 1
            pro.save()
            for i in range(0, int(tenure)):
                inst = Installment()
                inst.saleID_id = obj.pk
                inst.emiAmount = obj.emiAmount
                inst.assignedTo_id = int(assignTo)
                inst.installmentDate = obj.installmentStartDate + relativedelta(months=+i)
                inst.save()
            cache.delete('SalesListCache')
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_sales_admin_api(request):
    if request.method == 'POST':
        try:

            customer = request.POST.get("customer")
            product = request.POST.get("product")
            emi = request.POST.get("emi")
            advance = request.POST.get("advance")
            tenure = request.POST.get("tenure")
            totalAmount = request.POST.get("totalAmount")
            remark = request.POST.get("remark")
            idate = request.POST.get("idate")
            assignTo = request.POST.get("assignTo")
            saleID = request.POST.get("saleID")
            obj = Sale.objects.select_related().get(pk=int(saleID))
            try:
                photo = request.FILES["photo"]
                obj.deliveryPhoto = photo
            except:
                pass
            c = str(customer).split('@')
            cus = Customer.objects.select_related().get(pk=int(c[1]))
            p = str(product).split('@')
            prev_product = Product.objects.select_related().get(pk=obj.productID_id)
            prev_product.stock = (prev_product.stock + 1)
            prev_product.save()

            pro = Product.objects.select_related().get(pk=int(p[1]))

            obj.customerName = cus.name
            obj.customerID_id = cus.pk
            obj.productName = pro.name
            obj.productID_id = pro.pk
            obj.unit = pro.unitID
            obj.quantity = 1
            obj.rate = pro.sp
            obj.advancePaid = float(advance)
            obj.amountPaid = float(advance)
            obj.tenureInMonth = float(tenure)
            obj.emiAmount = float(emi)
            obj.totalAmount = float(totalAmount)
            obj.remark = remark

            obj.assignedTo_id = int(assignTo)
            obj.installmentStartDate = datetime.strptime(idate, '%d/%m/%Y')
            obj.save()


            pro.stock = pro.stock - 1
            pro.save()
            # for i in range(0, int(tenure)):
            #     inst = Installment()
            #     inst.saleID_id = obj.pk
            #     inst.emiAmount = obj.emiAmount
            #     inst.assignedTo_id = int(assignTo)
            #     inst.installmentDate = obj.installmentStartDate + relativedelta(months=+i)
            #     inst.save()
            cache.delete('SalesListCache')
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


def list_sales_api(request):
    try:
        o_list = []
        if cache.get('SalesListCache'):
            o_list = cache.get('SalesListCache')
        else:
            obj_list = Sale.objects.select_related().filter(isDeleted__exact=False).order_by('saleNo')
            for obj in obj_list:
                obj_dic = {
                    'ID': obj.pk,
                    'SaleID': obj.saleNo,
                    'CustomerName': obj.customerName,
                    'PaidAmount': obj.amountPaid,
                    'Detail': obj.saleNo + ' - ' + obj.customerName + ' @ ' + str(obj.pk),
                    'DisplayDetail': obj.saleNo + ' - ' + obj.customerName
                }
                o_list.append(obj_dic)
            cache.set('SalesListCache', o_list, timeout=None)
        return JsonResponse({'message': 'success', 'data': o_list}, safe=False)
    except:
        return JsonResponse({'message': 'error'}, safe=False)


@csrf_exempt
@transaction.atomic
def change_sales_status(request):
    if request.method == 'POST':
        id = request.POST.get("id")
        sale = Sale.objects.select_related().get(pk=int(id))
        sale.isClosed = not sale.isClosed
        sale.save()
        cache.delete('SalesListCache')
        return JsonResponse({'message': 'success'}, safe=False)


class SalesListByUserJson(BaseDatatableView):
    order_columns = ['deliveryPhoto', 'saleNo', 'customerName', 'productName', 'advancePaid', 'tenureInMonth',
                     'emiAmount',
                     'totalAmount',
                     'amountPaid', 'installmentStartDate', 'datetime']

    def get_initial_queryset(self):
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')

            return Sale.objects.select_related().filter(isDeleted__exact=False,
                                                        addedBy__user_ID_id__exact=self.request.user.pk,
                                                        datetime__range=(
                                                        sDate.date(), eDate.date() + timedelta(days=1)))

        except:

            return Sale.objects.select_related().filter(isDeleted__exact=False,
                                                        addedBy__user_ID_id__exact=self.request.user.pk)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(saleNo__icontains=search) | Q(customerName__icontains=search) | Q(
                    customerID__customerCode__icontains=search)
                | Q(productName__icontains=search) | Q(advancePaid__icontains=search) | Q(
                    tenureInMonth__icontains=search)
                | Q(emiAmount__icontains=search) | Q(totalAmount__icontains=search) | Q(amountPaid__icontains=search)
                | Q(datetime__icontains=search) | Q(remark__icontains=search) | Q(
                    installmentStartDate__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            photo = '''<img style="cursor:pointer" onclick="showImgModal('{}')" class="ui avatar image" src="{}">'''.format(
                item.deliveryPhoto.large.url, item.deliveryPhoto.thumbnail.url)
            action = '''<a data-inverted="" data-tooltip="Sales Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/sales_detail/{}/" class="ui circular facebook icon button green">
                    <i class="receipt icon"></i>
                  </a>
                 '''.format(item.pk),
            json_data.append([
                photo,  # escape HTML for security reasons
                escape(item.saleNo),
                escape(item.customerName),
                escape(item.productName),
                escape(item.advancePaid),
                escape(item.tenureInMonth),
                escape(item.emiAmount),
                escape(item.totalAmount),
                escape(item.amountPaid),
                escape(item.installmentStartDate.strftime('%d-%m-%Y')),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action
            ])
        return json_data


class SalesListAdminJson(BaseDatatableView):
    order_columns = ['deliveryPhoto', 'saleNo', 'customerName', 'productName', 'advancePaid', 'tenureInMonth',
                     'emiAmount',
                     'totalAmount',
                     'amountPaid', 'installmentStartDate', 'datetime', 'isClosed']

    def get_initial_queryset(self):
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')

            return Sale.objects.select_related().filter(isDeleted__exact=False,
                                                        datetime__range=(
                                                        sDate.date(), eDate.date() + timedelta(days=1)))

        except:

            return Sale.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(isClosed__icontains=search) | Q(customerName__icontains=search)
                | Q(saleNo__icontains=search) | Q(customerID__customerCode__icontains=search)
                | Q(productName__icontains=search) | Q(advancePaid__icontains=search) | Q(
                    tenureInMonth__icontains=search)
                | Q(emiAmount__icontains=search) | Q(totalAmount__icontains=search) | Q(amountPaid__icontains=search)
                | Q(datetime__icontains=search) | Q(remark__icontains=search) | Q(
                    installmentStartDate__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            photo = '''<img style="cursor:pointer" onclick="showImgModal('{}')" class="ui avatar image" src="{}">'''.format(
                item.deliveryPhoto.large.url, item.deliveryPhoto.thumbnail.url)
            if 'Admin' in self.request.user.groups.values_list('name', flat=True):
                action = '''<a data-inverted="" data-tooltip="Sales Edit" data-position="left center" data-variation="mini" style="font-size:10px;" href="/sales_edit_admin/{}/" class="ui circular facebook icon button purple">
                                    <i class="pen icon"></i>
                                  </a><a data-inverted="" data-tooltip="Sales Detail" data-position="left center" data-variation="mini" href="/sales_detail_admin/{}/" style="font-size:10px;" onclick = "GetPurchaseDetail('{}')" class="ui circular facebook icon button green">
                        <i class="receipt icon"></i>
                      </a>
                      <button data-inverted="" data-tooltip="Delete Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                        <i class="trash alternate icon"></i>
                      </button>'''.format(item.pk, item.pk, item.pk, item.pk),
            else:
                action = '''<a data-inverted="" data-tooltip="Sales Edit" data-position="left center" data-variation="mini" style="font-size:10px;" href="/sales_edit_admin/{}/" class="ui circular facebook icon button purple">
                                                    <i class="pen icon"></i>
                                                  </a><a data-inverted="" data-tooltip="Sales Detail" data-position="left center" data-variation="mini" href="/sales_detail_admin/{}/" style="font-size:10px;" onclick = "GetPurchaseDetail('{}')" class="ui circular facebook icon button green">
                                        <i class="receipt icon"></i>
                                      </a>
                                      '''.format(item.pk, item.pk, item.pk),

            if item.isClosed == True:
                isClosed = '<div class="ui mini green label"> Yes </div>'

            else:
                isClosed = '<div class="ui mini label red"> No </div>'

            json_data.append([
                photo,  # escape HTML for security reasons
                escape(item.saleNo),
                escape(item.customerName),
                escape(item.productName),
                escape(item.advancePaid),
                escape(item.tenureInMonth),
                escape(item.emiAmount),
                escape(item.totalAmount),
                escape(item.amountPaid),
                escape(item.installmentStartDate.strftime('%d-%m-%Y')),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                isClosed,
                action
            ])
        return json_data


# ------------------------------------Installments-----------------------------------

class InstallmentListByAdminJson(BaseDatatableView):
    order_columns = ['saleID.saleNo', 'saleID.customerName', 'emiAmount', 'installmentDate', 'paidAmount', 'isPaid',
                     'dueAmount', 'NextDueDate', 'remark', 'assignedTo.name', 'collectedBy.name', 'paymentReceivedOn']

    def get_initial_queryset(self):
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')

            return Installment.objects.select_related().filter(isDeleted__exact=False,
                                                               installmentDate__range=(sDate.date(), eDate.date()),

                                                               )
        except:

            return Installment.objects.select_related().filter(isDeleted__exact=False,
                                                               installmentDate__exact=datetime.today().date(),

                                                               )

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(saleID__saleNo__icontains=search) | Q(saleID__customerName__icontains=search) |
                Q(saleID__productName__icontains=search)
                | Q(assignedTo__name__icontains=search) | Q(collectedBy__name__icontains=search)
                | Q(installmentDate__icontains=search) | Q(remark__icontains=search)
                | Q(paidAmount__icontains=search) | Q(NextDueDate__icontains=search) | Q(dueAmount__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            action = ''
            if item.isPaid == False and item.saleID.isClosed == False:
                action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "editDetail('{}')" class="ui circular facebook icon button purple">
                      <i class="pen icon"></i>
                      </button>
                      <button data-inverted="" data-tooltip="Add Remark" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetRemark('{}')" class="ui circular facebook icon button blue">
                      <i class="clipboard outline icon"></i>
                      </button>
                      <button data-inverted="" data-tooltip="Take Installment" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetDetail('{}')" class="ui circular facebook icon button orange">
                        <i class="hand holding usd icon"></i>
                      </button>
                      <a data-inverted="" data-tooltip="Sales Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/sales_detail_admin/{}/" class="ui circular facebook icon button green">
                        <i class="receipt icon"></i>
                      </a>
                     '''.format(item.pk, item.pk, item.pk, item.saleID.pk)
            elif item.isPaid == True and item.saleID.isClosed == False:
                action = '''<button data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "editDetail('{}')" class="ui circular facebook icon button purple">
                      <i class="pen icon"></i>
                      </button> <button data-inverted="" data-tooltip="Add Remark" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetRemark('{}')" class="ui circular facebook icon button blue">
                      <i class="clipboard outline icon"></i>
                      </button>
                <a data-inverted="" data-tooltip="Sales Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/sales_detail_admin/{}/" class="ui circular facebook icon button green">
                                        <i class="receipt icon"></i>
                                      </a>
                                     '''.format(item.pk, item.pk, item.saleID.pk)
            else:
                action = '''<button data-inverted="" data-tooltip="Add Remark" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetRemark('{}')" class="ui circular facebook icon button blue">
                                      <i class="clipboard outline icon"></i>
                                      </button>
                                <a data-inverted="" data-tooltip="Sales Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/sales_detail_admin/{}/" class="ui circular facebook icon button green">
                                                        <i class="receipt icon"></i>
                                                      </a>
                                                     '''.format(item.pk, item.saleID.pk)

            if 'Admin' in self.request.user.groups.values_list('name', flat=True):
                action = action + '''
               <button data-inverted="" data-tooltip="Delete Detail" data-position="left center" data-variation="mini" style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                            <i class="trash alternate icon"></i>
                          </button>
               '''.format(item.pk)

            if item.isPaid == True:
                paid = '<div class="ui mini green label"> Yes </div>'
                r_time = escape(item.paymentReceivedOn.strftime('%d-%m-%Y %I:%M %p')),
                collectedBy = item.collectedBy.name
            else:
                paid = '<div class="ui mini label red"> No </div>'
                r_time = '-'
                collectedBy = '-'

            try:
                nextDueDate = escape(item.NextDueDate.strftime('%d-%m-%Y %I:%M %p')),
            except:
                nextDueDate = '-'
            json_data.append([
                escape(item.saleID.saleNo),
                escape(item.saleID.customerName),
                escape(item.emiAmount),
                escape(item.installmentDate.strftime('%d-%m-%Y')),
                escape(item.paidAmount),
                paid,
                escape(item.dueAmount),
                nextDueDate,
                escape(item.remark),
                escape(item.assignedTo.name),
                collectedBy,
                r_time,

                action
            ])
        return json_data


class InstallmentListByUserJson(BaseDatatableView):
    order_columns = ['saleID.saleNo', 'saleID.customerName', 'emiAmount', 'installmentDate', 'paidAmount', 'isPaid',
                     'dueAmount', 'NextDueDate', 'remark', 'paymentReceivedOn']

    def get_initial_queryset(self):
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')

            return Installment.objects.select_related().filter(isDeleted__exact=False,
                                                               assignedTo__user_ID_id__exact=self.request.user.pk,
                                                               installmentDate__range=(sDate.date(), eDate.date()),

                                                               )
        except:

            return Installment.objects.select_related().filter(isDeleted__exact=False,
                                                               assignedTo__user_ID_id__exact=self.request.user.pk,
                                                               installmentDate__exact=datetime.today().date(),

                                                               )

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(saleID__saleNo__icontains=search) |
                Q(saleID__customerName__icontains=search) | Q(saleID__productName__icontains=search)
                | Q(installmentDate__icontains=search) | Q(remark__icontains=search)
                | Q(paidAmount__icontains=search) | Q(NextDueDate__icontains=search) | Q(dueAmount__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            if item.isPaid == False and item.saleID.isClosed == False:
                action = '''<button data-inverted="" data-tooltip="Add Remark" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetRemark('{}')" class="ui circular facebook icon button blue">
                      <i class="clipboard outline icon"></i>
                      </button>
                      <button data-inverted="" data-tooltip="Take Installment" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetDetail('{}')" class="ui circular facebook icon button orange">
                        <i class="hand holding usd icon"></i>
                      </button>
                      <a data-inverted="" data-tooltip="Sales Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/sales_detail/{}/" class="ui circular facebook icon button green">
                        <i class="receipt icon"></i>
                      </a>
                     '''.format(item.pk, item.pk, item.saleID.pk),
            else:
                action = ''' <button data-inverted="" data-tooltip="Add Remark" data-position="left center" data-variation="mini" style="font-size:10px;" onclick = "GetRemark('{}')" class="ui circular facebook icon button blue">
                      <i class="clipboard outline icon"></i>
                      </button>
                <a data-inverted="" data-tooltip="Sales Detail" data-position="left center" data-variation="mini" style="font-size:10px;" href="/sales_detail/{}/" class="ui circular facebook icon button green">
                                        <i class="receipt icon"></i>
                                      </a>
                                     '''.format(item.pk, item.saleID.pk),

            if item.isPaid == True:
                paid = '<div class="ui mini green label"> Yes </div>'
                r_time = escape(item.paymentReceivedOn.strftime('%d-%m-%Y %I:%M %p')),
            else:
                paid = '<div class="ui mini label red"> No </div>'
                r_time = '-'

            try:
                nextDueDate = escape(item.NextDueDate.strftime('%d-%m-%Y %I:%M %p')),
            except:
                nextDueDate = '-'
            json_data.append([
                escape(item.saleID.saleNo),
                escape(item.saleID.customerName),
                escape(item.emiAmount),
                escape(item.installmentDate.strftime('%d-%m-%Y')),
                escape(item.paidAmount),
                paid,
                escape(item.dueAmount),
                nextDueDate,
                escape(item.remark),
                r_time,

                action
            ])
        return json_data


def get_installment_detail(request):
    id = request.GET.get('id')
    instance = get_object_or_404(Installment, id=id)
    remarks = InstallmentRemark.objects.select_related().filter(installmentID_id=instance.pk,
                                                                isDeleted__exact=False).order_by(
        'datetime')
    r_list = []
    for r in remarks:
        r_dic = {
            'ID': r.pk,
            'Remark': r.remark,
            'Latitude': r.latitude,
            'Longitude': r.longitude,
            'AddedBy': r.addedBy.name,
            'Photo': r.addedBy.photo.thumbnail.url,
            'AddedOn': r.datetime.strftime('%d-%m-%Y %I:%M %p')
        }
        r_list.append(r_dic)

    data = {
        'ID': instance.pk,
        'SaleID': instance.saleID.saleNo,
        'SaleNo': instance.saleID.pk,
        'EMIAmount': instance.emiAmount,
        'PaidAmount': instance.paidAmount,
        'DueAmount': instance.dueAmount,
        'AssignTo': instance.assignedTo_id,
        'Remark': instance.remark,
        'InstallmentDate': instance.installmentDate.strftime('%d/%m/%Y'),
        'Name': instance.saleID.customerName,
        'Amount': instance.emiAmount,
        'Remarks': r_list
    }
    return JsonResponse({'data': data}, safe=False)


@transaction.atomic
@csrf_exempt
def delete_installment_api(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            ins = Installment.objects.select_related().get(pk=int(id))
            obj = Sale.objects.select_related().get(pk=ins.saleID.pk)
            obj.amountPaid = (obj.amountPaid - ins.paidAmount)
            obj.save()
            ins.isDeleted = True
            ins.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def add_installment_api(request):
    if request.method == 'POST':
        try:
            ID = request.POST.get("ID")
            paidAmount = request.POST.get("paidAmount")
            dueAmount = request.POST.get("dueAmount")
            rdate = request.POST.get("rdate")
            remark = request.POST.get("remark")
            htmlLat = request.POST.get("htmlLat")
            htmlLong = request.POST.get("htmlLong")
            ins = Installment.objects.select_related().get(pk=int(ID))
            obj = Sale.objects.select_related().get(pk=ins.saleID.pk)
            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            ins.paidAmount = float(paidAmount)
            ins.isPaid = True
            ins.remark = remark
            ins.paymentReceivedOn = datetime.today().now()
            ins.collectedBy_id = user.pk
            ins.dueAmount = float(dueAmount)
            ins.latitude = htmlLat
            ins.longitude = htmlLong
            try:
                ins.NextDueDate = datetime.strptime(rdate, '%d/%m/%Y')
            except:
                pass
            ins.save()
            obj.amountPaid = (obj.amountPaid + float(paidAmount))
            obj.save()
            rem = InstallmentRemark()
            rem.installmentID_id = ins.pk
            rem.remark = remark
            rem.latitude = htmlLat
            rem.longitude = htmlLong
            rem.addedBy_id = user.pk
            rem.save()
            try:
                if float(dueAmount) > 0:
                    new_ins = Installment()
                    new_ins.saleID_id = obj.pk
                    new_ins.assignedTo_id = user.pk
                    if float(dueAmount) > 0:
                        new_ins.emiAmount = float(dueAmount)
                    else:
                        new_ins.emiAmount = float(obj.emiAmount)
                    new_ins.installmentDate = datetime.strptime(rdate, '%d/%m/%Y')
                    new_ins.save()

            except:
                pass

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def add_new_installment_api(request):
    if request.method == 'POST':
        try:
            newSaleID = request.POST.get("newSaleID")
            newInstallmentAmount = request.POST.get("newInstallmentAmount")
            newInstallmentDate = request.POST.get("newInstallmentDate")
            newAssignTo = request.POST.get("newAssignTo")
            newRemark = request.POST.get("newRemark")
            htmlLat = request.POST.get("htmlLat")
            htmlLong = request.POST.get("htmlLong")
            ins = Installment()

            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            ins.saleID_id = int(newSaleID)
            ins.installmentDate = datetime.strptime(newInstallmentDate, '%d/%m/%Y')
            ins.emiAmount = float(newInstallmentAmount)
            ins.assignedTo_id = int(newAssignTo)
            ins.remark = newRemark
            ins.latitude = htmlLat
            ins.longitude = htmlLong
            ins.save()
            rem = InstallmentRemark()
            rem.installmentID_id = ins.pk
            rem.remark = newRemark
            rem.latitude = htmlLat
            rem.longitude = htmlLong
            rem.addedBy_id = user.pk
            rem.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_installment_api(request):
    if request.method == 'POST':
        try:
            editID = request.POST.get("editID")
            editSaleID = request.POST.get("editSaleID")
            editRemark = request.POST.get("editRemark")
            editDueAmount = request.POST.get("editDueAmount")
            editPaidAmount = request.POST.get("editPaidAmount")
            editInstallmentAmount = request.POST.get("editInstallmentAmount")
            editInstallmentDate = request.POST.get("editInstallmentDate")
            editAssignTo = request.POST.get("editAssignTo")
            htmlLat = request.POST.get("htmlLat")
            htmlLong = request.POST.get("htmlLong")
            ins = Installment.objects.select_related().get(pk=int(editID))
            prev_amount = ins.paidAmount
            obj = Sale.objects.select_related().get(pk=ins.saleID.pk)
            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            ins.paidAmount = float(editPaidAmount)
            ins.assignedTo_id = int(editAssignTo)
            ins.remark = editRemark
            ins.collectedBy_id = user.pk
            ins.dueAmount = float(editDueAmount)
            ins.emiAmount = float(editInstallmentAmount)
            ins.longitude = htmlLong
            ins.longitude = htmlLong
            ins.installmentDate = datetime.strptime(editInstallmentDate, '%d/%m/%Y')
            if float(editPaidAmount) == 0.0:
                ins.isPaid = False

            else:
                ins.isPaid = True
                ins.collectedBy_id = user.pk
                ins.paymentReceivedOn = datetime.today().date()
            ins.save()
            obj.amountPaid = (obj.amountPaid - float(prev_amount) + float(editPaidAmount))
            obj.save()

            rem = InstallmentRemark()
            rem.installmentID_id = ins.pk
            rem.remark = editRemark
            rem.latitude = htmlLat
            rem.longitude = htmlLong
            rem.addedBy_id = user.pk
            rem.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


@transaction.atomic
@csrf_exempt
def add_installment_remark_api(request):
    if request.method == 'POST':
        try:
            idRemark = request.POST.get("idRemark")
            addRemark = request.POST.get("addRemark")
            htmlLat = request.POST.get("htmlLat")
            htmlLong = request.POST.get("htmlLong")
            ins = Installment.objects.select_related().get(pk=int(idRemark))
            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            rem = InstallmentRemark()
            rem.installmentID_id = ins.pk
            rem.remark = addRemark
            rem.latitude = htmlLat
            rem.longitude = htmlLong
            rem.addedBy_id = user.pk
            rem.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


# -------------------------------------------- # collection Report-----------------------------------

def get_collection_user_report_api(request):
    user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)

    customer_objs = Customer.objects.select_related().filter(isDeleted__exact=False, addedBy_id=user.pk)
    sale_objs = Sale.objects.select_related().filter(isDeleted__exact=False, addedBy_id=user.pk)
    today_inst = Installment.objects.select_related().filter(isDeleted__exact=False, assignedTo_id=user.pk,
                                                             installmentDate__icontains=datetime.today().date())
    collection = Installment.objects.select_related().filter(isDeleted__exact=False, collectedBy_id=user.pk,
                                                             installmentDate__icontains=datetime.today().date(),
                                                             isPaid__exact=True)

    c_total = 0.0
    for c in collection:
        c_total = c_total + c.paidAmount

    data = {
        'customerCount': customer_objs.count(),
        'salesCount': sale_objs.count(),
        'todayInstallmentCount': today_inst.count(),
        'collection': c_total
    }
    return JsonResponse({'data': data}, safe=False)


def get_admin_report_api(request):
    customer_objs = Customer.objects.select_related().filter(isDeleted__exact=False)
    sale_objs = Sale.objects.select_related().filter(isDeleted__exact=False)
    today_inst = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                             installmentDate__icontains=datetime.today().date())
    collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                             installmentDate__icontains=datetime.today().date(),
                                                             isPaid__exact=True)

    c_total = 0.0
    for c in collection:
        c_total = c_total + c.paidAmount

    data = {
        'customerCount': customer_objs.count(),
        'salesCount': sale_objs.count(),
        'todayInstallmentCount': today_inst.count(),
        'collection': c_total
    }
    return JsonResponse({'data': data}, safe=False)


def get_last_three_days_collection_report_for_admin_api(request):
    today = datetime.today().date()
    last_first_date = datetime.today().date() - timedelta(days=1)
    last_second_date = datetime.today().date() - timedelta(days=2)
    last_third_date = datetime.today().date() - timedelta(days=3)

    today_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                   installmentDate__icontains=today,
                                                                   isPaid__exact=True).aggregate(Sum('paidAmount'))
    first_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                   installmentDate__icontains=last_first_date,
                                                                   isPaid__exact=True).aggregate(Sum('paidAmount'))
    second_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                    installmentDate__icontains=last_second_date,
                                                                    isPaid__exact=True).aggregate(
        Sum('paidAmount', default=0))
    third_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                   installmentDate__icontains=last_third_date,
                                                                   isPaid__exact=True).aggregate(
        Sum('paidAmount', default=0))
    month_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                   installmentDate__year=today.year,
                                                                   installmentDate__month=today.month,
                                                                   isPaid__exact=True).aggregate(
        Sum('paidAmount', default=0))

    if today_collection['paidAmount__sum'] == None:
        to_c = 0.0
    else:
        to_c = today_collection['paidAmount__sum']
    if first_collection['paidAmount__sum'] == None:
        f_c = 0.0
    else:
        f_c = first_collection['paidAmount__sum']

    if second_collection['paidAmount__sum'] == None:
        s_c = 0.0
    else:
        s_c = second_collection['paidAmount__sum']

    if third_collection['paidAmount__sum'] == None:
        t_c = 0.0
    else:
        t_c = third_collection['paidAmount__sum']

    if month_collection['paidAmount__sum'] == None:
        m_c = 0.0
    else:
        m_c = month_collection['paidAmount__sum']
    data = {
        'today': today,
        'last_first_date': last_first_date,
        'last_second_date': last_second_date,
        'last_third_date': last_third_date,
        'today_collection': to_c,
        'first_collection': f_c,
        'second_collection': s_c,
        'third_collection': t_c,
        'month_collection': m_c,

    }
    return JsonResponse({'data': data}, safe=False)


def get_last_three_days_collection_report_for_user_api(request):
    today = datetime.today().date()
    last_first_date = datetime.today().date() - timedelta(days=1)
    last_second_date = datetime.today().date() - timedelta(days=2)
    last_third_date = datetime.today().date() - timedelta(days=3)
    user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
    first_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                   paymentReceivedOn__icontains=last_first_date,
                                                                   isPaid__exact=True,
                                                                   collectedBy_id__exact=user.pk).aggregate(
        Sum('paidAmount'))
    second_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                    paymentReceivedOn__icontains=last_second_date,
                                                                    isPaid__exact=True,
                                                                    collectedBy_id__exact=user.pk).aggregate(
        Sum('paidAmount', default=0))
    third_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                   paymentReceivedOn__icontains=last_third_date,
                                                                   isPaid__exact=True,
                                                                   collectedBy_id__exact=user.pk).aggregate(
        Sum('paidAmount', default=0))
    month_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                   paymentReceivedOn__year=today.year,
                                                                   paymentReceivedOn__month=today.month,
                                                                   isPaid__exact=True,
                                                                   collectedBy_id__exact=user.pk).aggregate(
        Sum('paidAmount', default=0))

    if first_collection['paidAmount__sum'] == None:
        f_c = 0.0
    else:
        f_c = first_collection['paidAmount__sum']

    if second_collection['paidAmount__sum'] == None:
        s_c = 0.0
    else:
        s_c = second_collection['paidAmount__sum']

    if third_collection['paidAmount__sum'] == None:
        t_c = 0.0
    else:
        t_c = third_collection['paidAmount__sum']

    if month_collection['paidAmount__sum'] == None:
        m_c = 0.0
    else:
        m_c = month_collection['paidAmount__sum']
    data = {
        'today': today,
        'last_first_date': last_first_date,
        'last_second_date': last_second_date,
        'last_third_date': last_third_date,
        'first_collection': f_c,
        'second_collection': s_c,
        'third_collection': t_c,
        'month_collection': m_c,

    }
    return JsonResponse({'data': data}, safe=False)


def get_daily_collections_by_staff(request):
    users = StaffUser.objects.select_related().filter(isDeleted__exact=False, isActive__exact='Active').order_by('name')
    data = []
    for user in users:

        user_collection = Installment.objects.select_related().filter(isDeleted__exact=False,
                                                                      paymentReceivedOn__icontains=datetime.today().date(),
                                                                      isPaid__exact=True,
                                                                      collectedBy_id__exact=user.pk).aggregate(
            Sum('paidAmount'))
        user_collectables = Installment.objects.select_related().filter(
            installmentDate__icontains=datetime.today().date(), isDeleted__exact=False,
            assignedTo_id__exact=user.pk).aggregate(Sum('emiAmount'))

        if user_collection['paidAmount__sum'] == None:
            collection = 0.0
        else:
            collection = user_collection['paidAmount__sum']

        if user_collectables['emiAmount__sum'] == None:
            collectable = 0.0
        else:
            collectable = user_collectables['emiAmount__sum']
        try:
            pc = round(((collection / collectable) * 100), 2)
        except:
            pc = 0
        data_dic = {
            'Staff': user.name,
            'Collection': collection,
            'Collectable': collectable,
            'Percent': pc
        }
        data.append(data_dic)
    return JsonResponse({'data': data}, safe=False)


# ------------------------------------Documents------------------------------------------

@transaction.atomic
@csrf_exempt
def add_document_api(request):
    if request.method == 'POST':
        try:
            title = request.POST.get("title")
            doc = request.FILES["doc"]
            obj = Document()
            obj.title = title
            obj.uploadedFile = doc
            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            obj.addedBy_id = user.pk
            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


class DocumentListAdminJson(BaseDatatableView):
    order_columns = ['title', 'uploadedFile', 'addedBy', 'datetime']

    def get_initial_queryset(self):
        # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
        return Document.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(title__icontains=search) | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            if 'Admin' in self.request.user.groups.values_list('name', flat=True):
                action = '''<button  data-inverted="" data-tooltip="Edit Detail" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick = "GetUserDetails('{}')" class="ui circular facebook icon button green">
                    <i class="pen icon"></i>
                  </button>
                  <button  data-inverted="" data-tooltip="Delete" data-position="left center" data-variation="mini"  style="font-size:10px;" onclick ="delUser('{}')" class="ui circular youtube icon button" style="margin-left: 3px">
                    <i class="trash alternate icon"></i>
                  </button></td>'''.format(item.pk, item.pk),
            else:
                action = '''<button  class="ui mini label">Denied</a>'''
            docFile = '''<a href="{}" target="_blank" class="ui mini teal label">Preview</a>'''.format(
                item.uploadedFile.url)
            json_data.append([
                escape(item.title),
                docFile,
                escape(item.addedBy.name),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),
                action,

            ])

        return json_data


@transaction.atomic
@csrf_exempt
def delete_document(request):
    if request.method == 'POST':
        try:
            id = request.POST.get("userID")
            obj = Document.objects.select_related().get(pk=int(id))
            obj.isDeleted = True
            obj.save()
            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


def get_document_detail(request):
    id = request.GET.get('id')
    instance = get_object_or_404(Document, id=id)

    data = {
        'ID': instance.pk,
        'Title': instance.title,
    }
    return JsonResponse({'data': data}, safe=False)


@transaction.atomic
@csrf_exempt
def edit_document_api(request):
    if request.method == 'POST':
        try:
            Id = request.POST.get("EditUserId")
            title = request.POST.get("title")

            obj = Document.objects.select_related().get(id=int(Id))
            obj.title = title
            try:
                doc = request.FILES["doc"]
                obj.uploadedFile = doc
            except:
                pass

            user = StaffUser.objects.select_related().get(user_ID_id=request.user.pk)
            obj.addedBy_id = user.pk
            obj.save()

            return JsonResponse({'message': 'success'}, safe=False)
        except:
            return JsonResponse({'message': 'error'}, safe=False)


# Login/ Logout History

class LoginLogoutListAdminJson(BaseDatatableView):
    order_columns = ['userID', 'statusType', 'datetime']

    def get_initial_queryset(self):
        try:
            startDateV = self.request.GET.get("startDate")
            endDateV = self.request.GET.get("endDate")
            sDate = datetime.strptime(startDateV, '%d/%m/%Y')
            eDate = datetime.strptime(endDateV, '%d/%m/%Y')

            # if 'Admin' in self.request.user.groups.values_list('name', flat=True):
            return LoginAndLogoutStatus.objects.select_related().filter(isDeleted__exact=False, datetime__range=(
                sDate.date(), eDate.date() + timedelta(days=1)), )
        except:
            return LoginAndLogoutStatus.objects.select_related().filter(isDeleted__exact=False)

    def filter_queryset(self, qs):

        search = self.request.GET.get('search[value]', None)
        if search:
            qs = qs.filter(
                Q(userID__name__icontains=search) | Q(statusType__icontains=search) | Q(datetime__icontains=search)
            )

        return qs

    def prepare_results(self, qs):
        json_data = []
        for item in qs:
            json_data.append([
                escape(item.userID.name),
                escape(item.statusType),
                escape(item.datetime.strftime('%d-%m-%Y %I:%M %p')),

            ])

        return json_data

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
