import inspect
import re
import uuid
from datetime import date
from datetime import timedelta, datetime
from functools import wraps
from json import dumps

import django_rq
import jdatetime
import requests
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.http.response import HttpResponse
from kavenegar import *
from mongoengine.connection import get_connection
from rolepermissions.checkers import has_role
from rq.job import Job


def getFarsiMonthName(jalali):
    if jalali.month == 1: return "فروردین"
    if jalali.month == 2: return "اردیبهشت"
    if jalali.month == 3: return "خرداد"
    if jalali.month == 4: return "تیر"
    if jalali.month == 5: return "مرداد"
    if jalali.month == 6: return "شهریور"
    if jalali.month == 7: return "مهر"
    if jalali.month == 8: return "آبان"
    if jalali.month == 9: return "آذر"
    if jalali.month == 10: return "دی"
    if jalali.month == 11: return "بهمن"
    if jalali.month == 12: return "اسفند"


def sendSMS(to, template, token='https://zibal.ir', token2=None, token3=None, token10=None, token20=None):
    try:
        api = KavenegarAPI('TOKEN')
        api.verify_lookup({
            'receptor': to,
            'token': token,
            'token2': token2,
            'token3': token3,
            'token10': token10,
            'token20': token20,
            'template': template
        })
    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)


def sendNormalSMS(to, message):
    try:
        api = KavenegarAPI('TOKEN')
        api.sms_send({'sender': '10004346', 'receptor': to, 'message': message})

    except APIException as e:
        print(e)
    except HTTPException as e:
        print(e)


def authenticateAdminWithQueryString(request):
    request.META['HTTP_AUTHORIZATION'] = 'Bearer ' + request.GET.get('token', '')
    request.user = authenticate(request=request)
    if request.user is None or not request.user.is_authenticated():
        return False
    if has_role(request.user, 'admin') or has_role(request.user, 'operator'):
        return True
    return False


def toJalaliDateTime(d, time=True):
    if isinstance(d, date) and not isinstance(d, datetime):
        d = datetime(d.year, d.month, d.day)
    if d is None:
        return '-'
    if time is True:
        return jdatetime.datetime.fromgregorian(datetime=d).strftime("%Y/%m/%d-%H:%M:%S")
    else:
        return jdatetime.datetime.fromgregorian(datetime=d).strftime("%Y/%m/%d")


def toPrettyJalaliDateTime(d):
    if isinstance(d, date) and not isinstance(d, datetime):
        d = datetime(d.year, d.month, d.day)
    if d is None: return '-'
    return jdatetime.datetime.fromgregorian(datetime=d).aslocale('fa_IR').pretty()


def sendEmail(subject, html_message, reciever):
    try:
        send_mail(subject, html_message=html_message, message="salam", recipient_list=[reciever],
                  from_email='زیبال<info@zibal.ir>')
    except Exception as e:
        sendByTelegram('خطا در ارسال ایمیل ' + str(e))
        pass


def jsonResponse(data={}, status=200):
    return HttpResponse(dumps(data), status=status, content_type='application/json')


def sendByTelegram(message, sensetive=True, chatId=None):
    try:
        if sensetive == '2':
            sendByTelegramByChatId(message)
        else:
            requests.post("http://tg.zibal.ir/bot.php",
                          data={'message': message, 'sensetive': '1' if sensetive else '0', 'chatId': chatId},
                          timeout=5)
    except:
        sendNormalSMS("09022502050", message)


def sendByTelegramByChatId(message, chatId='-288710257'):
    try:
        requests.post("http://tg.zibal.ir/bot.php", data={'message': message, 'sensetive': chatId}, timeout=5)
    except:
        sendNormalSMS("09022502050", message)


def sendTelegram(user, message, buttons):
    try:
        requests.post("http://tg.zibal.ir/bot.php", json={
            'userId': user.id,
            'message': message,
            'buttons': buttons,
        })
    except:
        pass


def getClientIp(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def isHoliday(datetime):
    if datetime.weekday() == 4:  # Friday
        return True

    holidays = {
        8: [18, 19],  # Augest 2021
        9: [27],  # september 2021
        10: [5, 7, 24],  # october 2021
        11: [],  # november 2021
        12: [],  # december 2021
        1: [6],  # january 2022
        2: [15],  # febuary 2022
        3: [1, 20, 21, 22, 23, 24],  # march 2022
        4: [2],  # april 2021
        5: [4, 13],  # may 2021
        6: [5, 6],  # june 2021
        7: [21, 29],  # july 2021
    }

    if datetime.day in holidays[datetime.month]:
        return True
    return False


def addCheckDigit(upc_str, increment=0):
    upc_str = str(upc_str)
    odd_sum = 0
    even_sum = 0
    for i, char in enumerate(upc_str):
        j = i + 1
        if j % 2 == 0:
            even_sum += int(char)
        else:
            odd_sum += int(char)

    total_sum = (odd_sum * 3) + even_sum
    mod = total_sum % 10
    check_digit = 10 - mod + increment
    check_digit = check_digit % 10
    return upc_str + str(check_digit)


def convertFaNumbers(text):
    import re
    """
    This function convert Persian numbers to English numbers.

    Keyword arguments:
    input_str -- It should be string
    Returns: English numbers
    """
    mapping = {
        '۰': '0',
        '٠': '0',
        '۱': '1',
        '١': '1',
        '۲': '2',
        '٢': '2',
        '۳': '3',
        '٣': '3',
        '۴': '4',
        '٤': '4',
        '۵': '5',
        '٥': '5',
        '۶': '6',
        '٦': '6',
        '۷': '7',
        '٧': '7',
        '۸': '8',
        '٨': '8',
        '۹': '9',
        '٩': '9',
        '.': '.',
    }
    pattern = "|".join(map(re.escape, mapping.keys()))
    return re.sub(pattern, lambda m: mapping[m.group()], str(text))


def generateRandomId():
    import uuid
    return uuid.uuid4().hex[:5]


def getWeekDayName(weekday):
    weekdays = [
        'دوشنبه',
        'سه‌شنبه',
        'چهارشنبه',
        'پنجشنبه',
        'جمعه',
        'شنبه',
        'یکشنبه',
        'دوشنبه',
    ]
    return weekdays[weekday]


def getNewApiKey():
    string = uuid.uuid4().hex
    return string


def normalizeMobile(mobile: str) -> str:
    if mobile is None:
        return None
    mobile = convertFaNumbers(mobile)
    length = len(mobile)
    res = mobile
    if length == 13 and mobile.startswith('+98'):
        res = f"0{mobile[3:]}"
    elif length == 12 and mobile.startswith('98'):
        res = f"0{mobile[2:]}"
    elif length == 10 and not mobile.startswith("0"):
        res = f"0{mobile}"
    if len(res) != 11:
        return None
    return res


def validateMobileNumber(mobileNumber):
    mobileNumber = normalizeMobile(mobileNumber)
    if mobileNumber is None:
        return False
    try:
        match_object = re.match(r"(^09[0-9]{9}$)", mobileNumber)
    except Exception:
        return False
    return bool(match_object)


def validateEmail(email):
    if email is None:
        return False
    try:
        match_object = re.match(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)", email)
    except Exception:
        return False
    return bool(match_object)


def validateIban(iban):
    try:
        if len(iban) != 26 or not iban.startswith("IR"):
            return False

        code = iban[4:] + iban[:4]
        code = code.replace('I', '18').replace('R', '27')

        return int(code) % 97 == 1
    except:
        return False


def recaptchaVerify(action):
    def decorator(webservice):
        @wraps(webservice)
        def wrapper(request, *args, **kwargs):
            url = "https://www.google.com/recaptcha/api/siteverify"
            params = {
                'secret': 'SECRET',
                'response': request.POST.get('r'),
            }
            response = requests.post(url=url, params=params).json()
            if response['success'] is False or response['score'] < 0.6 or response['action'] != action:
                return jsonResponse({'message': 'لطفا مجددا تلاش کنید'}, 403)
            return webservice(request, *args, **kwargs)

        return wrapper

    return decorator


def get_GET_list_parameter(request, paramName, functionToApply=None):
    res = request.GET.getlist(paramName)
    if res == []:
        res = request.GET.getlist(paramName + "[]")
    if res is not None and type(res) is not list:
        res = [res]
    if functionToApply is not None and res is not None:
        return list(map(functionToApply, res))
    return res


def doAsync(path, priority, function, *args, **kwargs):
    try:
        q = django_rq.get_connection(priority)
        job = Job.create(function, args=args, kwargs=kwargs,
                         connection=q,
                         meta={'path_name': str(path) + "/" + str(inspect.stack()[1][3]), 'failures': 0, "time": 120})
        queue = django_rq.get_queue(priority)
        queue.enqueue_job(job)
    except Exception:
        sendByTelegram("خطا در صف کار ها - کار به صورت سینک انجام شد.")
        function(*args, **kwargs)


# @mongoAtomicTransaction()
# def healthyCheck(request, session):
#     h = errorLog(time=datetime.now(), error="meysamm")
#     h.save(session=session)
#     raise Exception


def mongoAtomicTransaction():
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            client = get_connection()
            with client.start_session() as s:
                s.start_transaction()
                result = function(*args, **kwargs, session=s)
                s.commit_transaction()

            return result

        return wrapper

    return decorator


def validateNationalLegalCode(a):
    f, d = a[:10], a[10:]
    res = 0
    lis = [29, 27, 23, 19, 17, 29, 27, 23, 19, 17]
    for a in range(10):
        res += (int(f[-1]) + 2 + int(f[a])) * lis[a]
    if res % 11 == 10:
        r = 0
    else:
        r = res % 11
    if r == int(d):
        return True
    else:
        return False


def mobile_length_validator(mobile):
    mobile = str(mobile)
    if len(mobile) < 10 or mobile[-10] != "9":
        return False
    else:
        return "0" + mobile[-10:]


def credit_card_validate(card):
    try:
        if re.match(r"(^[456]+[0-9]{15}$)", card) is None:
            return False
        elem_list = [2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2, 1]
        card = list(map(int, card))
        result = [a * b if a * b < 10 else ((a * b) - 9) for a, b in zip(card, elem_list)]
        if sum(result) % 10 == 0:
            return True
        else:
            return False
    except:
        return False


def deltaMiliSecond(end, start):
    """start and end are datetime instances"""
    diff = end - start
    millis = diff.days * 24 * 60 * 60 * 1000
    millis += diff.seconds * 1000
    millis += diff.microseconds / 1000
    return millis


def predictDate(date, getObj=False):
    while isHoliday(date) == True:
        date = date + timedelta(1)
    if getObj:
        return date
    return date.strftime("%Y/%m/%d"), jdatetime.datetime.fromgregorian(datetime=date).strftime("%Y/%m/%d")


def getWeekNumber(day):
    yearStart = jdatetime.datetime(year=day.year, month=1, day=1)
    deltaWeeks = ((day - yearStart).days - (7 - yearStart.weekday())) // 7 + 2
    if deltaWeeks == 53:
        deltaWeeks = 1
    return deltaWeeks


def getNextMonthStart(datetimeObject, georgian=True):
    jalaliDateTime = jdatetime.datetime.fromgregorian(datetime=datetimeObject)
    if jalaliDateTime.month <= 6:
        jalaliDateTime = jalaliDateTime + jdatetime.timedelta(days=31)
    else:
        jalaliDateTime = jalaliDateTime + jdatetime.timedelta(days=30)
    if georgian:
        return jalaliDateTime.replace(day=1, hour=0, minute=0, second=0, microsecond=0).togregorian()
    return jalaliDateTime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def isAyandeh(bankAccount):
    return bankAccount[4:7] == '062'


def isBankAccountTransferable(bankAccount):
    return not (bankAccount[4:7] == '062' and bankAccount[-13:-10] == '080')


def calculatePayaWage(x, returnSum=False, IBAN=None):
    if IBAN and isAyandeh(IBAN):
        wage = 0
    else:
        wage = max(min(x / 10000, 250000), 2000)
    if returnSum:
        return wage + x
    return wage


def getHumanizedSettlementDate(settlementDate):
    if settlementDate:
        if settlementDate.hour == 15 and settlementDate.minute == 45:
            settlementText = ' عصر'
        elif settlementDate.hour == 10 and settlementDate.minute == 45:
            settlementText = ' ظهر'
        elif settlementDate.hour == 3 and settlementDate.minute == 45:
            settlementText = ' صبح'
        else:
            settlementText = ' - ' + str(settlementDate.hour) + ':' + str(settlementDate.minute)
        return toJalaliDateTime(settlementDate, False) + settlementText
    return ' - '


def normalizeMobile(mobile: str) -> str:
    try:
        if mobile is None:
            return None
        mobile = convertFaNumbers(mobile)
        length = len(mobile)
        res = mobile
        if length == 13 and mobile.startswith('+98'):
            res = f"0{mobile[3:]}"
        elif length == 12 and mobile.startswith('98'):
            res = f"0{mobile[2:]}"
        elif length == 10 and not mobile.startswith("0"):
            res = f"0{mobile}"
        if len(res) != 11:
            return None
        return res
    except:
        return None
