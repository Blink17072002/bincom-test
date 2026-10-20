from django.urls import path

from .views import home, polling_unit_result, lga_result, new_polling_unit_result


urlpatterns = [
    path("", home, name="home"),
    path("polling-unit/", polling_unit_result, name="polling_unit_result"),
    path("lga/", lga_result, name="lga_result"),
     path("new-result/", new_polling_unit_result, name="new_polling_unit_result"),
]