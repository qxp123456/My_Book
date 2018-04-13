from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from comments.models import Comment
from books.models import Books
from users.models import Passport
from  django.views.decorators.csrf import csrf_exempt
import json
import redis
# Create your views here.

#设置过期时间
EXPIRE_TIME = 60*10
#链接redis数据库
pool = redis.ConnectionPool(host='localhost',port=6379,db=2)
redis_db = redis.Redis(connection_pool=pool)

@csrf_exempt
@require_http_methods(['GET','POST'])
def comment(request,books_id):
	book_id = books_id
	if request.method == 'GET':
		#先在redis里面寻找评论
		c = redis_db.get('comment_%s' % book_id)
		try:
			c=c.decode('utf-8')
		except:
			pass
		if c:
			return JsonResponse({
				'code':200,
				'data':json.loads(c),
			})
		else:
			#找不到，从数据库提取
			comment = Comment.objects.filter(book_id=book_id)
			data=[]
			for c in comment:
				data.append({
					'user_id': c.user_id,
					'content': c.content
				})
			res = {
				'code':200,
				'data':data,
			}
			try:
				redis_db.setex('comment_%s' %book_id,json.dump(data),EXPIRE_TIME)
			except Exception as e:
				print('e:',e)
			return JsonResponse(res)
	else:
		params = json.loads(request.body.decode('utf-8'))

		book_id = params.get('book_id')
		user_id = params.get('user_id')
		content = params.get('content')

		book = Books.objects.get(id=book_id)
		user = Passport.objects.get(id=user_id)

		comment = Comment(book=book,user=user,content=content)
		comment.save()
		
		return JsonResponse({
			'code':200,
			'msg':'评论成功',
		})
