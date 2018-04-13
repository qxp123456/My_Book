from hashlib import sha1

from django.db import models

from basemodel.basemodel import BaseModel


# Create your models here.



class PassportManger(models.Manager):
	def add_one_passport(self,username,password,email):
		'''添加用户信息'''
		passport = self.create(username = username,password = get_hash(password),email=email)
		return passport

	def get_one_passport(self,username,password):
		'''查找账户信息'''
		try:
			passport = self.get(username=username,password=get_hash(password))
		except self.model.DoesNotExist:
			passport = None
		return passport
	def check_passport(self,username):
		try:
			passport = self.get(username=username)
		except self.model.DoesNotExist:
			passport = None
		if passport:
			return True
		return False

class Passport(BaseModel):
	'''用户模型'''
	username = models.CharField(max_length=20,verbose_name='用户名')
	password = models.CharField(max_length=40,verbose_name='用户密码')
	email = models.EmailField(verbose_name='用户邮箱')
	is_active = models.BooleanField(default=False,verbose_name='激活状态')

	#用户表的管理器
	objects = PassportManger()

	class Meta:
		db_table = 's_user_count'
class AddressManager(models.Manager):
	'''地址模型管理器'''
	def get_default_address(self,passport_id):
		'''查询默认的指定地址'''
		try:
			addr = self.get(passport_id = passport_id,is_default=True)
		except self.model.DoesNotExist:
			addr = None
		return addr
	def add_one_address(self,passport_id,recipient_name,recipient_addr,zip_code,recipient_phone):
		'''添加地址'''
		addr = self.get_default_address(passport_id=passport_id)
		if addr:
			#存在默认地址
			is_default = False
		else:
			#不存在默认地址
			is_default = True
		#添加一个地址
		addr = self.create(passport_id=passport_id,
						   recipient_name = recipient_name,
						   recipient_phone =recipient_phone,
						   recipient_addr = recipient_addr,
						   zip_code =zip_code,
						   is_default=is_default)
		return addr

class Address(BaseModel):
	'''地址'''
	recipient_name = models.CharField(max_length=20,verbose_name='收件人')
	recipient_addr = models.CharField(max_length=256,verbose_name='收件地址')
	zip_code = models.CharField(max_length=9,verbose_name='邮政编码')
	recipient_phone = models.CharField(max_length=11,verbose_name='联系电话')
	is_default = models.BooleanField(default=False,verbose_name='是否默认')
	passport = models.ForeignKey('Passport',verbose_name='账户')

	objects = AddressManager()

	class Meta:
		db_table = 's_user_address'

def get_hash(str):
	'''取哈希值'''
	sh = sha1()
	sh.update(str.encode('utf8'))
	return sh.hexdigest()

