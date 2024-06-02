import requests
import urllib.parse
from msal import ConfidentialClientApplication
import json

class BusinessCentralAPIClient(requests.Session):

    CUSTOMER_TABLE = 'SQLCustomer'
    PRODUCT_TABLE = 'SQLProduct'

    def __init__(self, 
                 tenant_id, 
                 environment, 
                 company,
                 client_id,
                 client_secret,
                 scopes=['https://api.businesscentral.dynamics.com/.default']
                 ):
        super().__init__()

        self.tenant_id = tenant_id
        self.environment = environment
        self.company = company
        self.client_id = client_id
        self.client_secret = client_secret
        self.scopes = scopes
        self.base_url = f"https://api.businesscentral.dynamics.com/v2.0/{self.tenant_id}/{self.environment}/ODataV4/Company('{self.company}')/"
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.access_token = None
        self.token_type = None
        self.get_oauth_token()
        self.headers.update(
            {
                'Authorization': f'{self.token_type} {self.access_token}',
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        )

    def get_oauth_token(self):

        auth_client = ConfidentialClientApplication(
        client_id=self.client_id,
        client_credential=self.client_secret,
        authority=self.authority
        )   
    
        token_response = auth_client.acquire_token_for_client(scopes=self.scopes)

        if 'access_token' in token_response:

            self.access_token = token_response['access_token']   
            self.token_type = token_response['token_type'] 

        else:

            raise Exception(f'''Unable to obtain access token with parameters provided.
                             client_id : {self.client_id}
                             client_secret : {self.client_secret}
                             authority : {self.authority}''')
        
    def refresh_oauth_token(self):

        self.get_oauth_token()

    
    def request(self, url, method, params=None):

        endpoint = urllib.parse.urljoin(self.base_url,url)

        response = super().request(url=endpoint,method=method,headers=self.headers,params=params)

        if response.status_code == 401:

            self.refresh_oauth_token()
            
            response = super().request(url=endpoint,method=method,headers=self.headers,params=params)

        
        response.raise_for_status()

        if method == 'GET':

            nextLink = response.json().get('@odata.nextLink')

            while nextLink:

                nextLink_response = super().request(url=nextLink,method=method,headers=self.headers)
                nextLink_response.raise_for_status()

                response.json()['value'].extend(nextLink_response.json()['value'])

                nextLink = nextLink_response.json().get('@odata.nextLink')
            
            return response.json().get('value')

        return response.json()
    
    def create_parameters(self,createdAt,modifiedAt,orderBy,select,offset,limit,filterExpression):

        self.params = {}

        if createdAt:

            self.params.update(
                {
                    '$filter' : f'systemCreatedAt gt {createdAt}'
                }
            )
        
        if modifiedAt:

            if '$filter' in self.params:

                self.params['$filter'] =+ f' and ()systemModifiedAt gt {modifiedAt})'

            else:
                
                self.params.update(
                    {
                        '$filter' : f'systemModifiedAt gt {modifiedAt}'
                    }
                )

        if orderBy:

            self.params.update(
                {
                    '$orderby' : f'{orderBy}'
                }
            )

        if select:
            
            self.params.update(
                {
                    '$select' : f'{select}'
                }
            )

        if offset:

            self.params.update(
                {
                    '$skip' : f'{offset}'
                }
            )
        
        if limit:

            self.params.update(
                {
                    '$top' : f'{limit}'
                }

            )
        
        if filterExpression:

            if '$filter' in self.params:

                self.params['$filter'] =+ f' and ({filterExpression})'

            else:

                self.params.update(
                    {
                        '$filter':f'{filterExpression}'
                    }
                )
            
    
    def get_customers(self,createdAt=None,modifiedAt=None,orderBy=None,select=None,offset=None,limit=None,filterExpression=None):

        self.create_parameters(createdAt,modifiedAt,orderBy,select,offset,limit,filterExpression)

        return self.request(url=self.CUSTOMER_TABLE,method='GET',params=self.params)
    
    def get_products(self,createdAt=None,modifiedAt=None,orderBy=None,select=None,offset=None,limit=None,filterExpression=None):

        self.create_parameters(createdAt,modifiedAt,orderBy,select,offset,limit,filterExpression)

        return self.request(url=self.PRODUCT_TABLE,method='GET',params=self.params)
    
    def get_customer(self,customer_id):

        return self.get_customers(filterExpression=f"no eq '{customer_id}'")
    
    def get_product(self,product_id):

        return self.get_products(filterExpression=f"no eq '{product_id}'")

    


    