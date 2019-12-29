# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import requests
from config import BASE_URL, REFRESH_ENDPOINT

class User:
    """
        User object that contain his header 
    """
    bearer_token = ""
    refresh_token = ""
    # need to fill Authoritazion with current token provide by api
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 " +
        "(KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36",
        "Authorization":""
        }
    
    def __init__(self, bearer_token, refresh_token):
        self.bearer_token = bearer_token
        self.refresh_token = refresh_token
        self.refresh_header()

    def refresh_jwt(self):
        """
            Request jwt refresh
        """
        url = BASE_URL+REFRESH_ENDPOINT
        
        try:
            r = requests.post(url, json={'refresh':self.refresh_token}, headers=self.header)
            if r.status_code == 200:
                print("You are in!")
                self.bearer_token = r.json()['data']['access']
                self.refresh_token = r.json()['data']['refresh']
        except requests.exceptions.RequestException as e:
            print("Error refreshing JWT,  check tokens")
            print("Error {}".format(e))
            sys.exit(2)

    def get_header(self):
        return self.header

    def refresh_header(self):
        """
            Refresh jwt because it expired and returned
        """
        self.refresh_jwt()
        self.header["Authorization"] = 'Bearer ' + self.bearer_token

        return self.header

