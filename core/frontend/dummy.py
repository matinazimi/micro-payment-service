from django.contrib.auth.decorators import login_required
from core.service.dummy import dummyFunction
from core.service.utils import jsonResponse


@login_required
def dummy(request):
    dummyValue1 = request.POST.get("dummyValue1")
    dummyValue2 = request.POST.get("dummyValue2")
    result = dummyFunction(dummyValue1, dummyValue2)
    jsonResponse({"result": result}, status=200)
