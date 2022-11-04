from django.contrib import admin

# Register your models here.
from .models import *


class StaffGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'datetime', 'lastUpdatedOn', 'isDeleted']


admin.site.register(StaffGroup, StaffGroupAdmin)


class StaffUserAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'address', 'email', 'username', 'userPassword', 'group', 'isActive', 'datetime',
                    'lastUpdatedOn']


admin.site.register(StaffUser, StaffUserAdmin)


class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'datetime', 'lastUpdatedOn', 'isDeleted']


admin.site.register(Unit, UnitAdmin)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'datetime', 'lastUpdatedOn', 'isDeleted']


admin.site.register(Category, CategoryAdmin)


class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'datetime', 'lastUpdatedOn', 'isDeleted']


admin.site.register(Brand, BrandAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'stock', 'categoryID', 'brandID', 'unitID', 'cp', 'mrp', 'sp', 'datetime', 'lastUpdatedOn',
                    'isDeleted']


admin.site.register(Product, ProductAdmin)


class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'gst', 'address', 'datetime', 'lastUpdatedOn', 'isDeleted']


admin.site.register(Supplier, SupplierAdmin)


class PurchaseProductListAdmin(admin.TabularInline):
    model = PurchaseProduct
    extra = 0


class PurchaseAdmin(admin.ModelAdmin):
    search_fields = ['supplierName']
    list_display = ['supplierName', 'taxableAmount', 'gstAmount', 'otherCharges', 'invoiceDate', 'grandTotal',
                    'invoiceNumber', 'isDeleted', 'datetime', 'lastUpdatedOn']

    inlines = (PurchaseProductListAdmin,)


admin.site.register(Purchase, PurchaseAdmin)


class CustomerAdmin(admin.ModelAdmin):
    search_fields = ['name', 'customerCode', 'phoneNumber', 'district', 'address']
    list_display = ['name', 'customerCode', 'phoneNumber', 'district', 'address', 'addedBy', 'latitude', 'longitude',
                    'isDeleted', 'datetime', 'lastUpdatedOn']


admin.site.register(Customer, CustomerAdmin)


class InstallmentsListAdmin(admin.TabularInline):
    model = Installment
    extra = 0


class SalesAdmin(admin.ModelAdmin):
    list_display = ['customerName', 'productName', 'advancePaid', 'tenureInMonth', 'emiAmount', 'totalAmount',
                    'amountPaid', 'addedBy', 'isDeleted', 'datetime', 'lastUpdatedOn']

    inlines = (InstallmentsListAdmin,)


admin.site.register(Sale, SalesAdmin)


class LoginAndLogoutAdmin(admin.ModelAdmin):
    list_display = ['userID', 'statusType', 'isDeleted', 'datetime']


admin.site.register(LoginAndLogoutStatus, LoginAndLogoutAdmin)


class InstallmentListAdmin(admin.ModelAdmin):
    search_fields = ['saleID', 'emiAmount', 'assignedTo', 'collectedBy', 'remark']
    list_display = ['saleID', 'installmentDate', 'emiAmount', 'paidAmount', 'dueAmount', 'NextDueDate', 'remark',
                    'assignedTo',
                    'collectedBy', 'paymentReceivedOn', 'datetime']


admin.site.register(Installment, InstallmentListAdmin)
