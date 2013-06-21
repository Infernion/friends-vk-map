#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib

from google.appengine.api import urlfetch
from google.appengine.ext import ndb

import handler
import model


KEY = '3720247'
SECRET = 'uOmPND7Xogaafizp6Xah'
REDIRECT_URI = r'http://friends-on-map.appspot.com/auth/vk'

class Auth(handler.Base):
  """ Auth handler.

Args:
code: Get var with auth code from vk.

Returns:
Auths user and redirects him to home page.
"""
  def get(self):
      self.get_token()
      user_info = self.url_fetch(
                                 method="users.get",
                                 fields="uid,first_name,last_name,city,country,photo_rec")

      name, countryid, cityid, photo_url = ('%s %s' % (user_info['first_name'], user_info['last_name']),
                                            user_info['country'],
                                            user_info['city'],
                                            user_info['photo_rec'])
      country = self.get_country(countryid)
      city = self.get_city(cityid)

      friends = self.url_fetch(
                               method="friends.get",
                               fields="uid,first_name,last_name,country,city,photo")

      self.response.set_cookie('uid', self.uid)

      user = model.User()
      user.populate(name=name,
                    uid=self.uid,
                    city=city,
                    country=country,
                    photo=photo_url,
                    friends=friends,
                    token=self.token)
      user.key = ndb.Key(model.User, user.uid)
      user.put()
      self.redirect('/map')

  def get_token(self):
      code = self.request.get('code')
      payload = urllib.urlencode({
          'redirect_uri': REDIRECT_URI,
          'client_secret': SECRET,
          'code': code,
          'client_id': KEY})
      self.token = urlfetch.fetch(
          url='https://oauth.vk.com/access_token?%s' % payload,
          method=urlfetch.GET).content
      token_json = json.loads(self.token)
      self.token = token_json['access_token']
      self.uid = str(token_json['user_id'])
      return self.uid

  def get_country(self, id):
      return (self.url_fetch(method="places.getCountryById",
                             cids=id))['name']

  def get_city(self, id):
      return (self.url_fetch(method="places.getCityById",
                             cids=id))['name']

  def url_fetch(self, cids="", method="", fields=""):
      value_json = urlfetch.fetch(
          url='https://api.vk.com/method/%s?uid=%s&cids=%s&fields=%s&access_self.token=%s' % (method, self.uid, cids, fields, self.token),
          method=urlfetch.POST).content
      if method == "friends.get":
          return (json.loads(value_json))['response']
      return (json.loads(value_json))['response'][0]
