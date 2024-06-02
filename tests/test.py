from dotenv import load_dotenv
from os import getenv
from src.business_central_api_client import BusinessCentralAPIClient
from rich import print


load_dotenv('/.env')

APIClient = BusinessCentralAPIClient(

    tenant_id = getenv('TENANT_ID'),
    environment = getenv('ENVIRONMENT'),
    company = getenv('COMPANY'),
    client_id = getenv('CLIENT_ID'),
    client_secret = getenv('CLIENT_SECRET')

)


customers = APIClient.get_customers()
