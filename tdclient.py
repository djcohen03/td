import sys
import urllib
import requests
import datetime
from db.models import *

class TDClient(object):
    ''' Client For Fetching Data from the TD Ameritrade Data API
    '''
    def __init__(self, refreshtoken, clientid):
        '''
        '''
        self.host = 'https://api.tdameritrade.com'
        self.refreshtoken = refreshtoken
        self.clientid = '%s@AMER.OAUTHAP' % clientid
        self.authenticate()

    def request(self, method, path, data={}):
        ''' Do a GET or POST Request with the given path and (optional) data
        '''
        if method == 'get':
            url = '%s%s?%s' % (self.host, path, urllib.urlencode(data))
            response = requests.get(url=url, headers=self.headers).json()
        elif method == 'post':
            url = self.host + path
            response = requests.post(url=url, data=data, headers=self.headers).json()
        else:
            raise Exception('Invalid HTTP Method: %s' % method)

        if 'error' in response:
            error = response['error']
            raise Exception(error)
        else:
            return response

    def isauthenticated(self):
        ''' Determine if the current session is authenticated by hitting a
            simple endpoint
        '''
        try:
            self.request('get', '/v1/accounts')
            return True
        except:
            return False

    def authenticate(self):
        ''' Does an initial authentication with TD's Refresh API
        '''
        # Reset the headers:
        self.headers = {}

        # Make the POST Reauthentication Request:
        path = '/v1/oauth2/token'
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refreshtoken,
            'client_id': self.clientid
        }
        response = self.request('post', path, data)

        # Save the Authentication Token & Authorization Headers:
        self.token = response['access_token']
        self.headers = {'Authorization': 'Bearer %s' % self.token}

        # Save the Expiration Time:
        seconds = response['expires_in']
        now = datetime.datetime.now()
        self.expiration = now + datetime.timedelta(0, seconds)

        print 'Successfully Authenticated TD\'s API, until %s' % self.expiration

    def optionschain(self, symbol):
        ''' Gets the Full Options Chain for the Given Symbol
        '''
        path = '/v1/marketdata/chains'
        args = {'symbol': symbol}
        return self.request('get', path, args)

    @classmethod
    def gettoken(cls, redirect='http://localhost', username='DJCOHEN0115'):
        ''' Step-By-Step Token Refresh Process
        '''
        # Generate the URL:
        args = urllib.urlencode({
            'redirect_uri': redirect,
            'client_id': username + '@AMER.OAUTHAP',
            'response_type': 'code'
        })
        url = 'https://auth.tdameritrade.com/auth?%s' % args
        print 'Visit the following Website And Sign In With Your Account: %s' % url

        code = urllib.unquote(raw_input('Enter code: '))

        tdurl = 'https://developer.tdameritrade.com/authentication/apis/post/token-0'
        print 'Visit The Following Website (May need to log in): %s' % tdurl
        print 'Enter The Following, and hit "Send":'
        print '\tgrant_type: authorization_code'
        print '\taccess_type: offline'
        print '\tclient_id: %s' % username
        print '\tredirect_uri: %s' % redirect
        print '\tcode: %s' % code

        # Do token import:
        return cls.importtoken()

    @classmethod
    def importtoken(cls):
        ''' Import token directly into the database
        '''
        # Gather Token Args:
        tokenstr = raw_input('Enter Refresh Token: ')
        today = datetime.date.today()

        # Create & Add Token to the Database:
        token = Token(token=tokenstr, date=today)
        session.add(token)
        session.commit()

        print 'Imported %s' % token
        return token



if __name__ == '__main__':
    if (len(sys.argv) > 1) and (sys.argv[1] == '--import'):
        # Allow User to Import Token Directly By Pasting:
        TDClient.importtoken()
    else:
        # Base Case, User Upload, Prompted Step-By-Step Thru Entire Process:
        TDClient.gettoken()
