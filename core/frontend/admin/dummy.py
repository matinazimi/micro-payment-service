from rolepermissions.decorators import has_role_decorator

from core.service.dummy import dummyFunction
from core.service.utils import jsonResponse


@has_role_decorator(['admin', 'operator'])
def dummy(request):
    dummyValue1 = request.POST.get("dummyValue1")
    dummyValue2 = request.POST.get("dummyValue2")
    result = dummyFunction(dummyValue1, dummyValue2)
    jsonResponse({"result": result}, status=200)
