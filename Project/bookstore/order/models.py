from django.db import models

# Create your models here.
from basemodel.basemodel import BaseModel

class OrderInfoManager(models.Manager):
	pass

class OrderInfo(BaseModel):
	'''订单信息模型'''
	PAY_METHOD_CHOICES = (
		(1,'货到付款'),
		(2,'微信支付'),
		(3,'支付宝'),
		(4,'银联支付')
	)
	PAY_METHODS_ENUM = {
		'CASH':1,
		'WEIXIN':2,
		'ALIPAY':3,
		'UNIONPAY':4,
	}
	ORDER_STATUS_CHOICES = (
		(1,'待支付'),
		(2,'待发货'),
		(3,'待收货'),
	)
