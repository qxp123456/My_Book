from django.template import Library

#创建一个Library类的对象

register = Library()

#创建一个过滤器函数
@register.filter
def order_status(status):
	'''返回订单状态对应的字符串'''
	status_dict = {
		1:'带支付',
		2:'代发货',
		3:'待收货',
		4:'带评论',
		5:'待评价',
	}

	return status_dict