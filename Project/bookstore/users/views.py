from django.http import JsonResponse
from django.shortcuts import render,redirect
import re
from users.models import Passport, Address
from django.core.urlresolvers import reverse
from utils.decorators import login_required

# Create your views here.

def register(request):
	return render(request, 'users/register.html')

def register_handle(request):
	print('cccc')
	'''用户信息注册'''
	username = request.POST.get('user_name')
	password = request.POST.get('pwd')
	email = request.POST.get('email')

	# 数据校验
	if not all([username, password, email]):
		print('2222')
		# 有数据为空
		return render(request, 'users/register.html', {'errmsg': '参数不能为空!'})

	if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
		print('333')
		# 邮箱不合法
		return render(request, 'users/register.html', {'errmsg': '邮箱不合法!'})

	# 添加信息
	passport = Passport.objects.add_one_passport(username=username,password=password,email=email)
	return redirect(reverse('books:index'))
	# return render(request,'books/index.html')

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
	print(username,password,remember)
	#数据校验
	if not all([username,password,remember]):
		return JsonResponse({'res':2})

	#数据处理
	passport = Passport.objects.get_one_passport(username=username,password=password)

	if passport:
		#获取session中的url_path
		next_url = request.session.get('url_path',reverse('books:index'))
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
	books_li = []
	context = {
		'addr':addr,
		'page':'user',
		'books_li':books_li
	}
	return  render(request,'users/user_center_info.html',context)

