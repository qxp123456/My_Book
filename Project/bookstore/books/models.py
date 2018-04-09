from django.db import models
from tinymce.models import HTMLField

from basemodel.basemodel import BaseModel
from books.enums import *


class HeroInfo(models.Model):
	hcontent = HTMLField()

class BooksManager(models.Manager):
	#排序
	def get_books_by_type(self,type_id,limit=None,sort = 'default'):
		if sort == 'new':
			order_by = ('-creat_time',)
		elif sort == 'hot':
			order_by = ('-seles',)
		elif sort == 'price':
			order_by = ('price',)
		else:
			order_by = ('-pk',)

		#查询数据
		books_li = self.filter(type_id=type_id).order_by(*order_by)

		#查询结果集的限制
		if limit:
			books_li = books_li[:limit]
		return books_li

	def get_books_by_id(self,books_id):
		'''根据id取商品信息'''
		try:
			books = self.get(id=books_id)
		except self.model.DoesNotExist:
			books = None
		return books

class Books(BaseModel):
	books_type_chioces = ((k,v) for k,v in BOOKS_TYPE.items()) #图数类型
	status_choices = ((k,v) for k,v in STATUS_CHOICE.items()) #图书状态
	type_id = models.SmallIntegerField(default=PYTHON,choices=books_type_chioces,verbose_name='商品种类')
	name = models.CharField(max_length=20,verbose_name='商品名称')
	desc = models.CharField(max_length=128,verbose_name='商品简介')
	price = models.DecimalField(max_digits=10,decimal_places=2,verbose_name='商品价格')
	unite = models.CharField(max_length=20,verbose_name='商品单位')
	stock = models.IntegerField(default=1,verbose_name='商品库存')
	seles = models.IntegerField(default=0,verbose_name='商品销量')
	detail = HTMLField(verbose_name='商品详情')
	image = models.ImageField(upload_to='books',verbose_name='商品图片')
	status = models.SmallIntegerField(default=ONLINE,choices=status_choices,verbose_name='商品状态')

	objects = BooksManager()


	class Meta:
		db_table = 's_books'

