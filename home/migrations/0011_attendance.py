# Generated by Django 3.2.16 on 2022-12-07 19:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0010_collection_collectiondatetime'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('registerType', models.CharField(blank=True, max_length=200, null=True)),
                ('login_remark', models.TextField(blank=True, null=True)),
                ('logout_remark', models.TextField(blank=True, null=True)),
                ('other_remark', models.TextField(blank=True, null=True)),
                ('login_latitude', models.CharField(default='0.0', max_length=200)),
                ('logout_latitude', models.CharField(default='0.0', max_length=200)),
                ('login_longitude', models.CharField(default='0.0', max_length=200)),
                ('logout_longitude', models.CharField(default='0.0', max_length=200)),
                ('isLogIn', models.BooleanField(default=False)),
                ('isLogOut', models.BooleanField(default=False)),
                ('loginDateTime', models.DateTimeField(blank=True, null=True)),
                ('logoutDateTime', models.DateTimeField(blank=True, null=True)),
                ('login_location', models.TextField(blank=True, null=True)),
                ('logout_location', models.TextField(blank=True, null=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('lastUpdatedOn', models.DateTimeField(auto_now=True)),
                ('isDeleted', models.BooleanField(default=False)),
                ('staffID', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='staffID', to='home.staffuser')),
            ],
            options={
                'verbose_name_plural': 'i) Login/Logout List',
            },
        ),
    ]
