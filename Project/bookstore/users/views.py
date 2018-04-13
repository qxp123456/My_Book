from PIL import ImageDraw
from django.core.mail import send_mail
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render,redirect
import re

from django_redis import get_redis_connection

from books.models import Books
from bookstore import settings
from order.models import OrderInfo, OrderGoods
from users.models import Passport, Address
from django.core.urlresolvers import reverse
from utils.decorators import login_required

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from users.tasks import send_active_email

# Create your views here.

def register(request):
	return render(request, 'users/register.html')



def login(request):
	'''登录页面'''
	username = ''
	checked = ''
	context = {
		'username' :username,
		'checked':checked,
	}
	return render(request,'users/login.html')

def login_check(request):
	'''获取数据'''
	username = request.POST.get('username')
	password = request.POST.get('password')
	remember = request.POST.get('remember')
	verifycode = request.POST.get('verifycode')
	print(username,password,remember,verifycode)
	#数据校验
	if not all([username,password,remember]):
		return JsonResponse({'res':2})

	if verifycode.upper() != request.session['verifycode']:
		return JsonResponse({'res': 2})

	#数据处理
	passport = Passport.objects.get_one_passport(username=username,password=password)

	if passport:
		#获取session中的url_path
		# next_url = request.session.get('url_path',reverse('books:index'))
		next_url = reverse('books:index')  # /user/
		jres = JsonResponse({'res':1,'next_url':next_url}) #返回给前台处理

		#是否记住密码
		if remember == 'true':
			#记住用户名
			jres.set_cookie('username',username,max_age=7*24*3600)
		else:
			#不记住用户名
			jres.delete_cookie('username')
			#记住用户的登录状态
		request.session['islogin'] = True
		request.session['username'] = username
		request.session['passport_id'] = passport.id
		return jres
	else:
		return JsonResponse({'res':0})


#用户退出
def logout(request):
	'''用户退出登录'''
	request.session.flush()
	#跳转到首页
	return redirect(reverse('books:index'))

@login_required
def user(request):
	'''用户信息'''
	passport_id = request.session.get('passport_id')
	#获取信息
	addr = Address.objects.get_default_address(passport_id=passport_id)

	# 获取用户的最近浏览信息
	con = get_redis_connection('default')
	key = 'history_%d' % passport_id
	# 取出用户最近浏览的5个商品的id
	history_li = con.lrange(key, 0, 4)
	books_li = []

	for id in history_li:
		books = Books.objects.get_books_by_id(books_id=id)
		books_li.append(books)

	context = {
		'addr':addr,
		'page':'user',
		'books_li':books_li
	}
	return  render(request,'users/user_center_info.html',context)


@login_required
def address(request):
	'''用户中心'''
	# 获取登陆用户的id
	passport_id = request.session.get('passport_id')

	if request.method == 'GET':
		# 显示地址页面
		addr = Address.objects.get_default_address(passport_id=passport_id)
		return render(request, 'users/user_center_site.html', {'addr': addr, 'page': 'address'})
	else:
		# 接收数据
		recipient_name = request.POST.get('username')
		recipient_addr = request.POST.get('addr')
		zip_code = request.POST.get('zip_code')
		recipient_phone = request.POST.get('phone')

		# 进行校验
		if not all([recipient_name, recipient_addr, zip_code, recipient_phone]):
			return render(request, 'users/user_center_site.html', {'errmsg': '参数不能为空'})

		# 添加收货地址
		print('+++++++++++++++')
		Address.objects.add_one_address(passport_id=passport_id,
										recipient_addr=recipient_addr,
										recipient_name=recipient_name,
										zip_code=zip_code,
										recipient_phone=recipient_phone
										)
		# 返回应答
		return redirect(reverse('user:address'))

@login_required
def order(request):
	'''用户中心，订单也'''
	'''查询用户的订单信息'''
	passport_id = request.session.get('passport_id')

	#获取订单信息
	order_li = OrderInfo.objects.filter(passport_id=passport_id)

	#便利获取订单的商品信息
	for order in order_li:
		#根据订单id查询订单商品信息
		order_id = order.order_id
		order_books_li = OrderGoods.objects.filter(order_id=order_id)

		#计算商品小计
		for order_books in order_books_li:
			count = order_books.count
			price = order_books.price
			amount = count * price

			#保存订单中的商品小计
			order_books.amount = amount

		#给order对象动态增加一个order_books_li 保存订单中的商品信息
		order.order_books_li = order_books_li

	context={
		'order_li':order_li,
		'page': 'order'
	}
	return render(request,'users/user_center_order.html',context)


def register_handle(request):

	username = request.POST.get('user_name')
	password = request.POST.get('pwd')
	email = request.POST.get('email')

	# 进行数据校验
	if not all([username, password, email]):
		# 有数据为空
		return render(request, 'users/register.html', {'errmsg':'参数不能为空!'})

	# 判断邮箱是否合法
	if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
		# 邮箱不合法
		return render(request, 'users/register.html', {'errmsg':'邮箱不合法!'})

	p = Passport.objects.check_passport(username=username)

	if p:
		return render(request, 'users/register.html', {'errmsg': '用户名已存在！'})

	# 进行业务处理:注册，向账户系统中添加账户
	# Passport.objects.create(username=username, password=password, email=email)
	passport = Passport.objects.add_one_passport(username=username, password=password, email=email)

	# 生成激活的token itsdangerous
	serializer = Serializer(settings.SECRET_KEY, 3600)
	token = serializer.dumps({'confirm':passport.id}) # 返回bytes
	token = token.decode()

	#异步发送
	# send_active_email.delay(token, username, email)

	#同步 给用户的邮箱发激活邮件
	send_mail('尚硅谷书城用户激活', '', settings.EMAIL_FROM, [email], html_message='<a href="http://127.0.0.1:8000/user/active/%s/">http://127.0.0.1:8000/user/active/</a>' % token)

	# 注册完，还是返回注册页。
	return redirect(reverse('books:index'))


def verifycode(request):
	#引入绘图模块
	from PIL import Image,ImageDraw,ImageFont
	import random
	#定义变量，用于画面的北京颜色，宽，高
	bgcolor = (random.randrange(20,100),random.randrange(20,100),255)
	width = 100
	height = 25
	#创建画面对象
	im = Image.new('RGB',(width,height),bgcolor)
	draw = ImageDraw.Draw(im)
	#创建画笔对象的point()绘制噪点
	for i in range(0,100):
		xy = (random.randrange(0,width),random.randrange(0,height))
		fill = (random.randrange(0,255),255,random.randrange(0,255))
		draw.point(xy,fill=fill)
	#定义验证码的备选值
	str1 = 'ABCD123EFGHIJK456LMNOPQRS789TUVWXYZ0'
	#随机选取四个值作为验证码
	rand_str = ""
	for i in range(0,4):
		rand_str += str1[random.randrange(0,len(str1))]
	#构造字体对象
	font = ImageFont.truetype('/usr/share/fonts/truetype/ubuntu-font-family/Ubuntu-M.ttf',15)

	#构造字体颜色
	fontcolor = (255, random.randrange(0, 255), random.randrange(0, 255))

	#绘制四个字
	draw.text((5,2),rand_str[0],font=font,fill=fontcolor)
	draw.text((25,2), rand_str[1], font=font, fill=fontcolor)
	draw.text((50,2), rand_str[2], font=font, fill=fontcolor)
	draw.text((55,2), rand_str[3], font=font, fill=fontcolor)

	#释放画笔
	del draw
	#存放session,用于验证
	request.session['verifycode'] = rand_str

	#内存文件操作
	import io
	buf = io.BytesIO()
	#将图片保存在内存中,文件为png

	im.save(buf,'png')
	return HttpResponse(buf.getvalue(), 'image/png')

#用户激活
def register_active(request,token):
	'''用户账户激活'''
	serializer = Serializer(settings.SECRET_KEY,3600)
	try:
		info = serializer.loads(token)
		passport_id = info['confirm']
		#进行用户激活
		passport = Passport.objects.get(id=passport_id)
		passport.is_active = True
		passport.save()
		#跳转的登录页
		return redirect(reverse('user:login'))
	except SignatureExpired:
		return HttpResponse('链接已过期')


