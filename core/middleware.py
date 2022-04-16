import json
import traceback

from django.core.exceptions import PermissionDenied, FieldError
from django.utils.decorators import method_decorator
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.debug import sensitive_post_parameters
from oauth2_provider.views import TokenView

from core.models import User
from core.service.utils import jsonResponse, validateMobileNumber, validateEmail, recaptchaVerify


class ExceptionMiddleware(MiddlewareMixin):

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            return jsonResponse(
                {'message': exception.__str__() or 'شما اجازه دسترسی به این قسمت را ندارید!', 'success': False}, 403)
        if isinstance(exception, FieldError):
            if not exception.args:
                return jsonResponse({'message': 'مقادیر ورودی را بررسی کنید!', 'success': False}, 400)
            else:
                return jsonResponse(exception.args[0], 400)

        print(traceback.format_exc())
        return jsonResponse(
            {'message': 'خطای داخلی سرور، زیبال این خطا را بررسی و برطرف خواهد کرد', 'status': False, 'result': -1},
            500)


class JSONMiddleware(MiddlewareMixin):
    """
    Process application/json requests data from GET and POST requests.
    """

    def process_request(self, request):

        if 'CONTENT_TYPE' in request.META and 'application/json' in request.META['CONTENT_TYPE']:
            # load the json data
            body_unicode = request.body.decode('utf-8')
            try:
                data = json.loads(body_unicode)
            except:
                data = body_unicode

            # for consistency sake, we want to return
            # a Django QueryDict and not a plain Dict.
            # The primary difference is that the QueryDict stores
            # every value in a list and is, by default, immutable.
            # The primary issue is making sure that list values are
            # properly inserted into the QueryDict.  If we simply
            # do a q_data.update(data), any list values will be wrapped
            # in another list. By iterating through the list and updating
            # for each value, we get the expected result of a single list.
            # q_data = QueryDict('', mutable=True)
            # for key in data:
            #     value = data.get(key)
            #     # if isinstance(value, list):
            #     #     # need to iterate through the list and update
            #     #     # so that the list does not get wrapped in an
            #     #     # additional list.
            #     #     for x in value:
            #     #         q_data.update({key: x})
            #     # else:
            #     q_data.update({key: value})

            if request.method == 'POST':
                request.POST = data

        return None


class TokenViewZibal(TokenView):
    @method_decorator(sensitive_post_parameters('password'))
    @method_decorator(recaptchaVerify('login'))
    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        try:
            request.POST = request.POST.copy()
            if validateMobileNumber(username):
                request.POST['username'] = User.objects.get(mobile=username).username
            elif validateEmail(username):
                request.POST['username'] = User.objects.get(email=username).username
        except User.MultipleObjectsReturned:
            pass
        except User.DoesNotExist:
            pass
        response = super(TokenViewZibal, self).post(request, *args, **kwargs)
        res = json.loads(response.content.decode('utf-8'))
        res['message'] = 'نام کاربری یا رمزعبور وارد شده صحیح نیست'
        response.content = json.dumps(res).encode('utf-8')
        logger.activity(request, 'login.failed')
