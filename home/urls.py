from django.urls import path
from .views import *
from .apiView import *

urlpatterns = [
    # pages
    path('home/', homepage, name='homepage'),
    path('', loginPage, name='loginPage'),
    # path('logout/', user_logout, name='logout'),
    path('postLogin/', postLogin, name='UserLogin'),

    # collection
    path('collection_home/', collection_home, name='collection_home'),
    path('customer_list_admin/', customer_list_admin, name='customer_list_admin'),
    path('customer_list/', customer_list, name='customer_list'),
    path('customer_add/', customer_add, name='customer_add'),
    path('customer_add_admin/', customer_add_admin, name='customer_add_admin'),
    path('sales_add/', sales_add, name='sales_add'),
    path('sales_add_admin/', sales_add_admin, name='sales_add_admin'),
    # path('sales_edit_admin/<int:id>/', sales_edit_admin, name='sales_edit_admin'),
    path('sales_list/', sales_list, name='sales_list'),
    path('sales_list_admin/', sales_list_admin, name='sales_list_admin'),
    path('document_list_admin/', document_list_admin, name='document_list_admin'),
    path('report_admin/', report_admin, name='report_admin'),
    path('installment_report_admin/', installment_report_admin, name='installment_report_admin'),

    # path('customer_detail/<int:id>/', customer_detail, name='customer_detail'),
    # path('customer_detail_admin/<int:id>/', customer_detail_admin, name='customer_detail_admin'),
    # path('customer_edit_admin/<int:id>/', customer_edit_admin, name='customer_edit_admin'),
    # path('sales_detail/<int:id>/', sales_detail, name='sales_detail'),
    # path('installment_list/', installment_list, name='installment_list'),
    # path('my_profile/', my_profile, name='my_profile'),
    #
    # # admin
    # path('my_profile_admin/', my_profile_admin, name='my_profile_admin'),
    path('admin_home/', admin_home, name='admin_home'),
    path('user_list/', user_list, name='user_list'),
    # path('product_list/', product_list, name='product_list'),
    path('purchase_list/', purchase_list, name='purchase_list'),
    # path('purchase_add/', purchase_add, name='purchase_add'),
    path('supplier_add/', supplier_add, name='supplier_add'),
    # path('installment_list_admin/', installment_list_admin, name='installment_list_admin'),
    # path('sales_detail_admin/<int:id>/', sales_detail_admin, name='sales_detail_admin'),
    #
    # path('login_logout_report_admin/', login_logout_report_admin, name='login_logout_report_admin'),
    #
    # # api Staff
    path('api/add_staff_api/', add_staff_api, name='add_staff_api'),
    path('api/delete_staff_user/', delete_staff_user, name='delete_staff_user'),
    path('api/get_staff_user_detail/', get_staff_user_detail, name='get_staff_user_detail'),
    path('api/edit_staff_api/', edit_staff_api, name='edit_staff_api'),
    path('api/StaffUserListJson/', StaffUserListJson.as_view(), name='StaffUserListJson'),
    #
    # # api Product
    # path('api/list_product_api/', list_product_api, name='list_product_api'),
    # path('api/add_product_api/', add_product_api, name='add_product_api'),
    # path('api/delete_product/', delete_product, name='delete_product'),
    # path('api/get_product_detail/', get_product_detail, name='get_product_detail'),
    # path('api/edit_product_api/', edit_product_api, name='edit_product_api'),
    # path('api/ProductListJson/', ProductListJson.as_view(), name='ProductListJson'),
    #
    # # api Supplier
    # path('api/add_supplier_api/', add_supplier_api, name='add_supplier_api'),
    # path('api/delete_supplier/', delete_supplier, name='delete_supplier'),
    # path('api/get_supplier_detail/', get_supplier_detail, name='get_supplier_detail'),
    # path('api/edit_supplier_api/', edit_supplier_api, name='edit_supplier_api'),
    # path('api/SupplierListJson/', SupplierListJson.as_view(), name='SupplierListJson'),
    #
    # # api purchase
    #
    # path('api/add_purchase_api/', add_purchase_api, name='add_purchase_api'),
    # path('api/delete_purchase/', delete_purchase, name='delete_purchase'),
    # path('api/get_purchase_detail/<int:id>/', get_purchase_detail, name='get_purchase_detail'),
    # path('api/PurchaseListJson/', PurchaseListJson.as_view(), name='PurchaseListJson'),
    #
    # # api Customer
    #
    # path('api/delete_customer_api/', delete_customer_api, name='delete_customer_api'),
    # path('api/list_customer_api/', list_customer_api, name='list_customer_api'),
    # path('api/add_customer_api/', add_customer_api, name='add_customer_api'),
    # path('api/edit_customer_api/', edit_customer_api, name='edit_customer_api'),
    # path('api/CustomerListByUserJson/', CustomerListByUserJson.as_view(), name='CustomerListByUserJson'),
    # path('api/CustomerListAdminJson/', CustomerListAdminJson.as_view(), name='CustomerListAdminJson'),
    #
    # # sales
    # path('api/delete_sale_api/', delete_sale_api, name='delete_sale_api'),
    # path('api/add_sales_api/', add_sales_api, name='add_sales_api'),
    # path('api/add_sales_admin_api/', add_sales_admin_api, name='add_sales_admin_api'),
    # path('api/edit_sales_admin_api/', edit_sales_admin_api, name='edit_sales_admin_api'),
    # path('api/list_sales_api/', list_sales_api, name='list_sales_api'),
    # path('api/change_sales_status/', change_sales_status, name='change_sales_status'),
    # path('api/SalesListByUserJson/', SalesListByUserJson.as_view(), name='SalesListByUserJson'),
    # path('api/SalesListAdminJson/', SalesListAdminJson.as_view(), name='SalesListAdminJson'),
    #
    # # installments
    # path('api/InstallmentListByAdminJson/', InstallmentListByAdminJson.as_view(), name='InstallmentListByAdminJson'),
    # path('api/InstallmentListByUserJson/', InstallmentListByUserJson.as_view(), name='InstallmentListByUserJson'),
    # path('api/delete_installment_api/', delete_installment_api, name='delete_installment_api'),
    # path('api/get_installment_detail/', get_installment_detail, name='get_installment_detail'),
    # path('api/add_installment_api/', add_installment_api, name='add_installment_api'),
    # path('api/add_installment_remark_api/', add_installment_remark_api, name='add_installment_remark_api'),
    # path('api/add_new_installment_api/', add_new_installment_api, name='add_new_installment_api'),
    # path('api/edit_installment_api/', edit_installment_api, name='edit_installment_api'),
    #
    # # report dashboard
    # path('api/get_collection_user_report_api/', get_collection_user_report_api, name='get_collection_user_report_api'),
    # path('api/get_admin_report_api/', get_admin_report_api, name='get_admin_report_api'),
    # path('api/get_last_three_days_collection_report_for_admin_api/',
    #      get_last_three_days_collection_report_for_admin_api,
    #      name='get_last_three_days_collection_report_for_admin_api'),
    # path('api/get_last_three_days_collection_report_for_user_api/', get_last_three_days_collection_report_for_user_api,
    #      name='get_last_three_days_collection_report_for_user_api'),
    # path('api/get_daily_collections_by_staff/', get_daily_collections_by_staff, name='get_daily_collections_by_staff'),
    #
    # # documents
    # path('api/add_document_api/', add_document_api, name='add_document_api'),
    # path('api/delete_document/', delete_document, name='delete_document'),
    # path('api/get_document_detail/', get_document_detail, name='get_document_detail'),
    # path('api/edit_document_api/', edit_document_api, name='edit_document_api'),
    # path('api/DocumentListAdminJson/', DocumentListAdminJson.as_view(), name='DocumentListAdminJson'),
    #
    # # login and logout
    # path('api/LoginLogoutListAdminJson/', LoginLogoutListAdminJson.as_view(), name='LoginLogoutListAdminJson'),
    #
    # # change password
    # path('api/change_password_api/', change_password_api, name='change_password_api'),

]
