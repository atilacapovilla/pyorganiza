from django.urls import path

from apps.finance.views.card_views import CardList

urlpatterns = [
    path("cards/", CardList, name="cards"),
]
