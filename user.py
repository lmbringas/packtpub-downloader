# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import requests
from config import BASE_URL, AUTH_ENDPOINT

class User:
    """
        User object that contain his header 
    """
    username = ""
    password = ""
    # need to fill Authoritazion with current token provide by api
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
        "Authorization":""
        }
    
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.header["Authorization"] = self.get_token()
    
    def get_token(self):
        """
            Request auth endpoint and return user token  
        """
        url = BASE_URL+AUTH_ENDPOINT
        # use json paramenter because for any reason they send user and pass in plain text :'(  
        try:
            r = requests.post(url, json={'username':self.username, 'password':self.password})
            if r.status_code == 200:
                print("You are in!")
                return 'Bearer ' + r.json()['data']['access']
        except Exception as e:
            # except should happend when user and pass are incorrect
            print("Error login,  check user and password")
            print("Error {}".format(e))
        sys.exit(2)

    def get_header(self):
        return self.header

    def refresh_header(self):
        """
            Refresh jwt because it expired and returned
        """
        self.header["Authorization"] = self.get_token()

        return self.header

