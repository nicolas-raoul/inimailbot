# ###
# Copyright (c) 2010 Konstantinos Spyropoulos <inigo.aldana@gmail.com>
#
# This file is part of inimailbot
#
# inimailbot is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# inimailbot is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with inimailbot.
# If not, see http://www.gnu.org/licenses/.
# #####

import os, sys, logging, re, hashlib
from datetime import datetime
from urllib import quote_plus
from string import strip
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.1')
# Force Django to reload its settings.
from django.conf import settings
settings._target = None

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api.urlfetch import fetch
from google.appengine.api.urlfetch import Error

from receive_ankicrashes import AppVersion
from receive_ankicrashes import CrashReport
from receive_ankicrashes import HospitalizedReport
from receive_ankicrashes import Bug
from BeautifulSoup import BeautifulSoup

# Remove the standard version of Django
#for k in [k for k in sys.modules if k.startswith('django')]:
#    del sys.modules[k] 
#webapp.template.register_template_library('templatetags.basic_math')

class ShowCrashBody(webapp.RequestHandler):
	def get(self):
		crId = long(self.request.get('id'))
		cr = CrashReport.get_by_id(crId)
		m = re.search(r'^(.*--\&gt; END REPORT 1 \&lt;--).*$', cr.report, re.S)
		new_report = m.group(1)
		template_values = {'crash_body': cr.report,
				'new_crash_body': new_report}
		logging.info(cr.report)
		logging.info(new_report)
		path = os.path.join(os.path.dirname(__file__), 'templates/admin_ops_show.html')
		self.response.out.write(template.render(path, template_values))

###
# This class is used for bulk ad hoc operations in the DB, eg reparsing signatures, rebuilding the
# bugs table or adding new properties to the entities.
#
# Due to limitations of time and memory in the AppEngine, we can't process all the entities in a
# big loop, we have to work in batches. Each page loaded is a batch, following Next we can process
# the next one, until all are done.
##########
class AdminOps(webapp.RequestHandler):
#	@classmethod
#	def getCrashSignature2(cls, body):
#		result1 = ''
#		result2 = ''
#		m1 = re.search(r"Begin Stacktrace\s*(<br>\s*)*([^<\s][^<]*[^<\s])\s*<br>", body, re.M|re.U)
#		if m1 and m1.groups():# and m2 and m2.groups():
#			result1 = re.sub(r"\$[a-fA-F0-9@]*", "", m1.group(2))
#		m2 = re.search(r"<br>\s*(at\scom\.ichi2\.[^<]*[^<\s])\s*<br>", body, re.M|re.U)
#				           #"<br>\s*(at\scom\.ichi2\.anki\..*?\S)\s*<br>", body, re.M|re.U)
#		if m2 and m2.groups():# and m2 and m2.groups():
#			result2 = re.sub(r"\$[a-fA-F0-9@]*", "", m2.group(1))
#		return result1 + "\n" + result2
	def get(self):
		crashes_query = CrashReport.all()
		crashes = []
		page = int(self.request.get('page', 0))
		total_results = crashes_query.count(1000000)
		logging.info(total_results)
		last_page = max((total_results - 1) // 500, 0)
		logging.info(last_page)
		if page > last_page:
			page = last_page
		crashes = crashes_query.fetch(500, page*500)
		tags = {}
		for cr in crashes:
			#AppVersion.insert(cr.versionName, cr.crashTime)
			#cr.entityVersion = 1
			#cr.adminOpsflag = 0
			#cr.put()
			if cr.versionName in tags:
				tags[cr.versionName] = tags[cr.versionName] + 1
			else:
				tags[cr.versionName] = 1

		results_list=[]
		template_values = {'results_list': results_list,
				'tags': tags,
				'page': page,
				'last_page': last_page,
				'page_size': 500,
				'total_results': total_results}
		path = os.path.join(os.path.dirname(__file__), 'templates/admin_ops.html')
		self.response.out.write(template.render(path, template_values))

application = webapp.WSGIApplication(
		[(r'^/ankidroid_triage/admin_show.*$', ShowCrashBody),
		(r'^/ankidroid_triage/admin_ops$', AdminOps)],
		debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()

