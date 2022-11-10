from django.urls import path
from .views import *
from .apiView import *

urlpatterns = [
    # pages
    path('home/', homepage, name='homepage'),
    path('', loginPage, name='loginPage'),
    path('logout/', user_logout, name='logout'),
    path('postLogin/', postLogin, name='UserLogin'),

    # collection
    path('collection_home/', collection_home, name='collection_home'),

    #
    # # admin
    path('my_profile/', my_profile, name='my_profile'),
    path('admin_home/', admin_home, name='admin_home'),
    path('user_list/', user_list, name='user_list'),

    path('party_group_list/', party_group_list, name='party_group_list'),
    path('party_list/', party_list, name='party_list'),
    path('bank_list/', bank_list, name='bank_list'),

    # # api Staff
    path('api/add_staff_api/', add_staff_api, name='add_staff_api'),
    path('api/delete_staff_user/', delete_staff_user, name='delete_staff_user'),
    path('api/get_staff_user_detail/', get_staff_user_detail, name='get_staff_user_detail'),
    path('api/edit_staff_api/', edit_staff_api, name='edit_staff_api'),
    path('api/StaffUserListJson/', StaffUserListJson.as_view(), name='StaffUserListJson'),

    # # api party group
    path('api/add_party_group_api/', add_party_group_api, name='add_party_group_api'),
    path('api/delete_part_group/', delete_part_group, name='delete_part_group'),
    path('api/get_party_group_detail/', get_party_group_detail, name='get_party_group_detail'),
    path('api/edit_part_group_api/', edit_part_group_api, name='edit_part_group_api'),
    path('api/PartyGroupListJson/', PartyGroupListJson.as_view(), name='PartyGroupListJson'),
    #
    # api Banks
    path('api/add_bank_api/', add_bank_api, name='add_bank_api'),
    path('api/BankListJson/', BankListJson.as_view(), name='BankListJson'),
    path('api/delete_bank/', delete_bank, name='delete_bank'),
    path('api/get_bank_detail/', get_bank_detail, name='get_bank_detail'),
    path('api/edit_bank_api/', edit_bank_api, name='edit_bank_api'),

    # # change password
    path('api/change_password_api/', change_password_api, name='change_password_api'),

]
