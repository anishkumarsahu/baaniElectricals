from django.contrib.auth.models import User
from django.db import models
from stdimage import StdImageField


# Create your models here.


class StaffGroup(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'a) User Group List'


class StaffUser(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    photo = StdImageField(upload_to='photo/img', blank=True, variations={
        'large': (600, 400),
        'thumbnail': (50, 50, True),
        'medium': (300, 200),
    }, delete_orphans=True)
    idProof = StdImageField(upload_to='photo/img', blank=True, variations={
        'large': (600, 400),
        'thumbnail': (50, 50, True),
        'medium': (300, 200),
    }, delete_orphans=True)
    phone = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    email = models.CharField(max_length=200, blank=True, null=True)
    username = models.CharField(max_length=200, blank=True, null=True)
    userPassword = models.CharField(max_length=200, blank=True, null=True)
    group = models.CharField(max_length=200, blank=True, null=True)
    user_ID = models.ForeignKey(User, blank=True, null=True, on_delete=models.CASCADE)
    isActive = models.CharField(max_length=200, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'b) User List'


class Unit(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'c) Unit List'


class Category(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'd) Category List'


class Brand(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'e) Brand List'


class Product(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    stock = models.FloatField(default=0.0)
    categoryID = models.CharField(max_length=200, blank=True, null=True)
    brandID = models.CharField(max_length=200, blank=True, null=True)
    unitID = models.CharField(max_length=200, blank=True, null=True)
    cp = models.FloatField(default=0.0)
    mrp = models.FloatField(default=0.0)
    sp = models.FloatField(default=0.0)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'f) Product List'


class Supplier(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=200, blank=True, null=True)
    gst = models.CharField(max_length=200, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'g) Supplier List'


class Purchase(models.Model):
    supplierID = models.ForeignKey(Supplier, blank=True, null=True, on_delete=models.CASCADE)
    supplierName = models.CharField(max_length=200, blank=True, null=True)
    taxableAmount = models.FloatField(default=0.0)
    gstAmount = models.FloatField(default=0.0)
    otherCharges = models.FloatField(default=0.0)
    roundOff = models.FloatField(default=0.0)
    grandTotal = models.FloatField(default=0.0)
    invoiceNumber = models.CharField(max_length=200, blank=True, null=True)
    invoiceDate = models.DateField(blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.supplierName

    class Meta:
        verbose_name_plural = 'h) Purchase List'


class PurchaseProduct(models.Model):
    purchaseID = models.ForeignKey(Purchase, blank=True, null=True, on_delete=models.CASCADE)
    productID = models.ForeignKey(Product, blank=True, null=True, on_delete=models.CASCADE)
    productName = models.CharField(max_length=200, blank=True, null=True)
    category = models.CharField(max_length=200, blank=True, null=True)
    quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=200, blank=True, null=True)
    rate = models.FloatField(default=0.0)
    gst = models.FloatField(default=0.0)
    total = models.FloatField(default=0.0)
    net = models.FloatField(default=0.0)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.productName

    class Meta:
        verbose_name_plural = 'i) Purchase Product List'


class Customer(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    customerCode = models.CharField(max_length=100, blank=True, null=True)
    district = models.CharField(max_length=100, blank=True, null=True)
    landmark = models.CharField(max_length=500, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    phoneNumber = models.CharField(max_length=100, blank=True, null=True)
    photo = StdImageField(upload_to='customer/img', blank=True, variations={
        'large': (600, 400),
        'thumbnail': (50, 50, True),
        'medium': (300, 200),
    }, delete_orphans=True)
    idProofFront = StdImageField(upload_to='customer/img', blank=True, variations={
        'large': (600, 400),
        'thumbnail': (50, 50, True),
        'medium': (300, 200),
    }, delete_orphans=True)
    idProofBack = StdImageField(upload_to='customer/img', blank=True, variations={
        'large': (600, 400),
        'thumbnail': (50, 50, True),
        'medium': (300, 200),
    }, delete_orphans=True)
    addedBy = models.ForeignKey(StaffUser, blank=True, null=True, on_delete=models.CASCADE)
    latitude = models.CharField(max_length=200, default='0.0')
    longitude = models.CharField(max_length=200, default='0.0')
    remark = models.CharField(max_length=500, blank=True, null=True)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'j).Customer List'


class Sale(models.Model):
    saleNo = models.CharField(max_length=200, blank=True, null=True)
    customerID = models.ForeignKey(Customer, blank=True, null=True, on_delete=models.CASCADE)
    productID = models.ForeignKey(Product, blank=True, null=True, on_delete=models.CASCADE)
    customerName = models.CharField(max_length=200, blank=True, null=True)
    productName = models.CharField(max_length=200, blank=True, null=True)
    quantity = models.IntegerField(default=0)
    unit = models.CharField(max_length=200, blank=True, null=True)
    rate = models.FloatField(default=0.0)
    advancePaid = models.FloatField(default=0.0)
    tenureInMonth = models.FloatField(default=0.0)
    emiAmount = models.FloatField(default=0.0)
    totalAmount = models.FloatField(default=0.0)
    amountPaid = models.FloatField(default=0.0)
    latitude = models.CharField(max_length=200, default='0.0')
    longitude = models.CharField(max_length=200, default='0.0')
    remark = models.CharField(max_length=500, blank=True, null=True)
    projectName = models.CharField(max_length=500, blank=True, null=True)
    installmentStartDate = models.DateField(blank=True, null=True)
    deliveryPhoto = StdImageField(upload_to='deliveryPhoto', blank=True, variations={
        'large': (600, 400),
        'thumbnail': (50, 50, True),
        'medium': (300, 200),
    }, delete_orphans=True)
    addedBy = models.ForeignKey(StaffUser, blank=True, null=True, on_delete=models.CASCADE, related_name='AddedBy')
    assignedTo = models.ForeignKey(StaffUser, blank=True, null=True, on_delete=models.CASCADE,
                                   related_name='AssignedTo')
    isClosed = models.BooleanField(default=False)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return self.customerName

    class Meta:
        verbose_name_plural = 'k) Sales List'


class Installment(models.Model):
    saleID = models.ForeignKey(Sale, blank=True, null=True, on_delete=models.CASCADE)
    installmentDate = models.DateField(blank=True, null=True)
    emiAmount = models.FloatField(default=0.0)
    paidAmount = models.FloatField(default=0.0)
    dueAmount = models.FloatField(default=0.0)
    NextDueDate = models.DateField(blank=True, null=True)
    remark = models.CharField(max_length=500, blank=True, null=True)
    assignedTo = models.ForeignKey(StaffUser, blank=True, null=True, on_delete=models.CASCADE,
                                   related_name='AssignedToInstallment')
    collectedBy = models.ForeignKey(StaffUser, blank=True, null=True, on_delete=models.CASCADE,
                                    related_name='CollectedBy')
    paymentReceivedOn = models.DateTimeField(blank=True, null=True)
    latitude = models.CharField(max_length=200, default='0.0')
    longitude = models.CharField(max_length=200, default='0.0')
    isPaid = models.BooleanField(default=False)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.installmentDate)

    class Meta:
        verbose_name_plural = 'L) Installment Date List'


class InstallmentRemark(models.Model):
    installmentID = models.ForeignKey(Installment, blank=True, null=True, on_delete=models.CASCADE)
    remark = models.CharField(max_length=500, blank=True, null=True)
    latitude = models.CharField(max_length=200, default='0.0')
    longitude = models.CharField(max_length=200, default='0.0')
    addedBy = models.ForeignKey(StaffUser, blank=True, null=True, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.remark)

    class Meta:
        verbose_name_plural = 'M) Installment Remark'


class Document(models.Model):
    title = models.CharField(max_length=500, blank=True, null=True)
    uploadedFile = models.FileField(upload_to='Documents', blank=True, null=True)
    addedBy = models.ForeignKey(StaffUser, blank=True, null=True, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)
    isDeleted = models.BooleanField(default=False)

    def __str__(self):
        return str(self.title)

    class Meta:
        verbose_name_plural = 'N) Documents'


class LoginAndLogoutStatus(models.Model):
    userID = models.ForeignKey(StaffUser, blank=True, null=True, on_delete=models.CASCADE)
    statusType = models.CharField(max_length=100, blank=True, null=True)
    latitude = models.CharField(max_length=200, default='0.0')
    longitude = models.CharField(max_length=200, default='0.0')
    isDeleted = models.BooleanField(default=False)
    datetime = models.DateTimeField(auto_now_add=True, auto_now=False)
    lastUpdatedOn = models.DateTimeField(auto_now_add=False, auto_now=True)

    def __str__(self):
        return str(self.userID.name)

    class Meta:
        verbose_name_plural = 'O) Login-Logout'
