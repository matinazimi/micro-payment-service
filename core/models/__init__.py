from datetime import datetime

from django.db import models
from django.db.models import Q
from mongoengine import Q as Q_mongo
from django.db.models.fields import CharField, IntegerField, TextField, DateTimeField
from django.contrib.auth.models import AbstractUser
import core.models.mongoModels
import core.enum as Enum
from core.service.utils import toJalaliDateTime


class User(AbstractUser):
    STATUS_DEACTIVE = 0
    STATUS_ACTIVE = 1
    STATUS_REGISTRATION = 2
    TYPE_HAGHIGHI = 0
    TYPE_HOGHOOGHI = 1

    companyName = CharField(max_length=100, null=True)
    phone = CharField(max_length=11, null=True)
    mobile = CharField(max_length=11, null=True)
    mobileVerifiedAt = DateTimeField(null=True)
    transactionPerDay = IntegerField(null=True)
    posWantedNum = IntegerField(null=True)
    activityDesc = TextField(null=True)
    website = CharField(max_length=100, null=True)
    status = IntegerField(default=0)
    userType = IntegerField(default=0, null=True)
    operatorUserStatus = IntegerField(default=0, null=True)
    economyCode = CharField(max_length=20, null=True)
    address = CharField(max_length=120, null=True)
    postalCode = CharField(max_length=20, null=True)
    nationalCode = CharField(max_length=20, null=True)
    referralCode = CharField(max_length=120, null=True)
    checkoutDelayByDay = IntegerField(default=0)
    comment = TextField(null=True)
    maxWallets = IntegerField(default=0)
    mobileVerifyToken = IntegerField(null=True)
    verifyTokenExpireAt = DateTimeField(null=True)
    forgotPasswordVerifyToken = CharField(max_length=88, null=True)
    forgotPasswordVerifyTokenExpiredAt = DateTimeField(null=True)
    emailVerifyToken = CharField(max_length=88, null=True)
    emailVerifyTokenExpireAt = DateTimeField(null=True)
    emailVerifiedAt = DateTimeField(null=True)
    IPGLoyalty = IntegerField(null=True)
    userDataStatus = IntegerField(default=0)
    hubspotContactId = IntegerField(null=True,default=None)
    permissions = TextField(null=True)
    USER_DATA_STATUS_NOT_COMPLETE = 0#old 3 to 2 new. old2 to 4
    USER_DATA_STATUS_COMPLETING = 1
    USER_DATA_STATUS_COMPLETED = 2
    USER_DATA_STATUS_DATA_INVALID = 3
    USER_DATA_STATUS_DATA_SENT_TO_SHAPARAK = 4
    USER_DATA_STATUS_SHAPARAK_ACCEPTED = 5
    USER_DATA_STATUS_SHAPARAK_REJECTED = 6
    agreementIP = CharField(max_length=20,default=None,null=True)

    twoFactor = models.BooleanField(default=False)

    updatedAt = DateTimeField(auto_now=True,null=True)
    wageWallet = CharField(max_length=30, null=True)

    secondPassword = CharField(max_length=128, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.updatedAt = datetime.now()
        super(User, self).save(*args, **kwargs)


    @property
    def maskedMobile(self):
        if self.mobile is not None:
            return self.mobile[:4] + '****' + self.mobile[8:]
        return ""
    def getCheckoutDelayByDay(self):
        return 1
        if self.checkoutDelayByDay == 0:
            return Enum.Defaults.CHECKOUT_DAY.value
        return self.checkoutDelayByDay

    def getMaxWallets(self):
        if self.maxWallets == 0:
            return Enum.Defaults.MAX_WALLETS.value
        return self.maxWallets

    def getComments(self):
        comments = []
        for comment in self.comments.all():
            comments.append({
                'commenter': comment.commenter.username,
                'body': comment.body,
                'createdAt': toJalaliDateTime(comment.createdAt),
            })
        return comments

    def setLoyalty(self,loyalty):
        self.IPGLoyalty = loyalty
        self.save()

    def setHubspotContactId(self,contactId):
        self.hubspotContactId = contactId
        self.save()

    def getPermissions(self):
        if self.permissions == '' or self.permissions is None:
            return []
        permissions = self.permissions.split(",")
        return list(map(int,permissions))

    def hasPermissions(self,permissions):
        permissions = set(permissions)
        userPermissions = set(self.getPermissions())
        rootPermission = set([int(permission/100)*100 for permission in permissions])
        permissions = permissions.union(rootPermission)
        if len(set(permissions).intersection(userPermissions)) > 0:
            return True
    def setPermissions(self,permissions):
        self.permissions = ",".join(permissions)
        self.save()

    def deletePermissions(self,permissions):
        newPermissions = set(map(str,self.getPermissions())) - set(map(str,permissions))
        self.setPermissions(newPermissions)

    def addPermissions(self,permissions):
        newPermissions = set(self.getPermissions()).union(set(permissions))
        self.setPermissions(list(map(str,newPermissions)))

    @classmethod
    def getPermissionUsers(cls,permission):
        rootPermission = int(permission/100)*100
        users = list(cls.objects.filter(Q(permissions__contains=permission)|Q(permissions__contains=rootPermission)).values('id','companyName'))
        return users

    @classmethod
    def getById(cls,userId):
        try:
            return cls.objects.get(id=userId)
        except:
            return None

    @property
    def files(self):
        return core.models.mongoModels.File.objects.filter(Q_mongo(userId=self.id)|Q_mongo(allowedUsers__contains=self.id))

class File(models.Model):
    name = CharField(max_length=100)
    actualName = CharField(max_length=100, null=True)
    fileSize = IntegerField(null=True)
    type = IntegerField()
    user = models.ForeignKey(User,on_delete=models.DO_NOTHING)
    createdAt = models.DateTimeField(auto_now_add=True)
    ticketId = models.CharField(max_length=200,default=None,null=True)
    allowedUser = models.ForeignKey(User,on_delete=models.DO_NOTHING,related_name='allowedFiles',null=True)

    def setTicket(self,ticketId):
        self.ticketId = ticketId

class contactUS(models.Model):
    fullname = CharField(max_length=100)
    email = CharField(max_length=100)
    title = CharField(max_length=100, null=True)
    message = TextField(null=True)

class UserComment(models.Model):
    commentedOnUser = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='+')  # no backward relation
    type = models.IntegerField(null=True, default=0)
    body = models.TextField()
    createdAt = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('createdAt',)

    @classmethod
    def leaveComment(cls,userId,operatorUserId,reason,commentType,body):
        cls(
            commentedOnUser_id=userId,
            commenter_id=operatorUserId,
            reason=reason,
            type=commentType,
            body=body
        ).save()

    @classmethod
    def getUserFlowComments(cls, userId):
        stages = {
            1: [],
            2: [],
            3: []
        }
        comments = cls.objects.filter(commentedOnUser_id=userId)
        operators = {}
        for comment in comments:
            if operators.get(comment.commenter_id,None) is None:
                user = User.objects.get(id=comment.commenter_id)
                operators[user.id] = {
                    "operatorId": user.id,
                    "companyName": user.companyName,
                    "username": user.username
                }
            stages[comment.type].append({
                "user": operators[comment.commenter_id],
                "body": comment.body,
                "reason":comment.reason
            })
        return stages


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.IntegerField()
    value = models.IntegerField()

    class Meta:
        unique_together = ('user', 'type', )

    @staticmethod
    def getSetting(user, type):
        try:
            notifSetting = Notification.objects.get(user=user, type=type[0]).value
        except Notification.DoesNotExist:
            notifSetting = type[1]

        return notifSetting


class MySQLTest(models.Model):
    data = TextField()
    number = IntegerField()
    createdAt = DateTimeField()


class UserDevice(models.Model):
    participant = models.ForeignKey(User, on_delete=models.CASCADE)
    platform = models.CharField(max_length=20, choices=(('iOS', 'iOS'), ('Android', 'Android'), ("Web", "Web")))
    token = models.CharField(unique=True, max_length=200)

    @classmethod
    def addDevice(cls, user, platform, token):
        try:
            cls.objects.create(
                participant=user,
                platform=platform,
                token=token
            )
            return True
        except(Exception,):
            return False

