from django.urls import path

from goosetools.market.views import (
    all_order_sold,
    all_stack_sold,
    edit_order_price,
    item_sell,
    order_sold,
    orders,
    sell_all_items,
    sold,
    stack_change_price,
    stack_sell,
    stack_sold,
)

urlpatterns = [
    path("item/<int:pk>/sell", item_sell, name="item_sell"),
    path("stack/<int:pk>/sell", stack_sell, name="stack_sell"),
    path("stack/<int:pk>/change_price", stack_change_price, name="stack_change_price"),
    path("stack/<int:pk>/sold", stack_sold, name="stack_sold"),
    path("stack/<int:pk>/sold/all", all_stack_sold, name="all_stack_sold"),
    path("loc/<int:pk>/sell/all/", sell_all_items, name="sell_all"),
    path("order/<int:pk>/edit", edit_order_price, name="edit_order_price"),
    path("order/<int:pk>/sold", order_sold, name="order_sold"),
    path("order/<int:pk>/sold/all", all_order_sold, name="all_order_sold"),
    path("orders/", orders, name="orders"),
    path("sold/", sold, name="sold"),
]
