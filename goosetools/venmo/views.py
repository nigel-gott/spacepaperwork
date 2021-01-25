from bravado.client import SwaggerClient
from bravado.requests_client import RequestsClient
from bravado.swagger_model import load_file
from django.conf import settings
from django.shortcuts import render

swagger_file = load_file("goosetools/venmo/swagger.yml")


def venmo_client():
    host = settings.VENMO_HOST_URL
    requests_client = RequestsClient()
    api_token_header_name = swagger_file["securityDefinitions"]["api_key"]["name"]
    requests_client.set_api_key(
        host,
        settings.VENMO_API_TOKEN,
        param_name=api_token_header_name,
        param_in="header",
    )
    swagger_file["host"] = settings.VENMO_HOST_URL
    return SwaggerClient.from_spec(swagger_file, http_client=requests_client)


def transactions(request):
    venmo_server_client = venmo_client()
    venmo_user_balance_future = venmo_server_client.users.getUserBalance(
        discordId=request.gooseuser.discord_uid()
    )
    venmo_user = venmo_user_balance_future.response().result
    return render(request, "venmo/transactions.html", {"balance": venmo_user.balance})
