# -*- coding: utf-8 -*-

'''
    This file contain all url endpoint 
'''

# instead of variables should i change variables to a one big json of urls ? 

# this is base url where i do the requests
BASE_URL = "https://services.packtpub.com/"

# this is base url for static content
BASE_STATIC_URL = "https://static.packt-cdn.com/"

# URL to request jwt token, params by post are user and pass, return jwt token
AUTH_ENDPOINT = "auth-v1/users/tokens"

# URL to get all your books, two params that i change are offset and limit, method GET
PRODUCTS_ENDPOINT = "entitlements-v1/users/me/products?sort=createdAt:DESC&offset={offset}&limit={limit}"

# URL to get book information from id
PRODUCT_FROM_ID_ENDPOINT = "products/{id}/summary"

# URL to get types , param is  book id, method GET
URL_BOOK_TYPES_ENDPOINT = "products-v1/products/{book_id}/types"

# URL to get url file to download, params are book id and format of the file (can be pdf, epub, etc..), method GET
URL_BOOK_ENDPOINT = "products-v1/products/{book_id}/files/{format}"
