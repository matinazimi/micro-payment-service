from django.conf.urls import url

import core.frontend.admin.dummy
import core.frontend.dummy

urlpatterns = [
    url(r'^api/dummy/?$', core.frontend.dummy.dummy),
    url(r'^api/admin/dummy/?$', core.frontend.admin.dummy.dummy),



]