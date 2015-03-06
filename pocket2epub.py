#!/usr/bin/env python2
#-*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import web2epub
import StringIO

class MainPage(webapp2.RequestHandler):
  def get(self):
    token = '%s?token=3c461de3c&url=' % self.request.path
    token_len = len(token)
    uri = self.request.path_qs
    process_url = uri[token_len:]
    title = 'make'
    if uri.startswith(token):
        zipstream=StringIO.StringIO()
        web2epub.url2epub([process_url], outfile=zipstream)

        zipstream.seek(0)
        self.response.headers['Content-Type'] ='application/epub+zip'
#        self.response.headers['Content-Type'] ='application/octet-stream'
        Disposition = 'attachment; filename="%s.epub"' % title.encode('utf8')
        self.response.headers['Content-Disposition'] = Disposition
        self.response.out.write(zipstream.getvalue())

class Make2epub(webapp2.RequestHandler):
#  def get(self, token, url):
  def get(self, **args):
    print args
    self.response.out.write(args)



app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/make.epub', MainPage),
  (r'/<token>/test', Make2epub),
#  (r'/<token>/<url>', Make2epub),
#  (r'/(\S+)/(\S+)', Make2epub),
], debug=True)
