#! /usr/bin/env python
'''
Copyright (c) 2012 Max Tsai<haiching.tsai@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

import sys
import codecs
import commands
import os
import MySQLdb
import smtplib
import datetime
from email.mime.text import MIMEText
from xml.dom import minidom


class config:
	def dprint(self, msg):
		print "CONFIG: " + msg

	def __init__(self):
		stat, path = commands.getstatusoutput("pwd")
		self.path = path
		self.buildxml = self.path + "/build.xml"
		self.configxml = self.path + "/config.xml"
		self.configdoc = minidom.parse(self.configxml)
		self.buildoc = minidom.parse(self.buildxml)
		self.smtp_ipaddr = "172.16.0.10"
	
	def save_xml_file(self, filename, doc):
		f = open(filename, 'w')
		writer = codecs.lookup('utf-8')[3](f)
		doc.writexml(writer, encoding='utf-8')
		f.close()
	
	def get_build_attribute(self, tag_name, attr_name):
		self.buildoc = minidom.parse(self.buildxml)
		item = self.buildoc.getElementsByTagName(tag_name)
		return item[0].getAttribute(attr_name)
	
	def set_build_attribute(self, tag_name, attr_name, value):
		self.buildoc = minidom.parse(self.buildxml)
		item = self.buildoc.getElementsByTagName(tag_name)
		item[0].setAttribute(attr_name, value)
		self.save_xml_file(self.buildxml, self.buildoc)
	
	def get_force_build_attribute(self, tag_name, attr_name):
		self.configdoc = minidom.parse(self.configxml)
		item = self.configdoc.getElementsByTagName("force_build")
		return (item[0].getElementsByTagName(tag_name))[0].getAttribute(attr_name)
	
	def set_force_build_attribute(self, tag_name, attr_name, value):
		self.configdoc = minidom.parse(self.configxml)
		item = self.configdoc.getElementsByTagName("force_build")
		(item[0].getElementsByTagName(tag_name))[0].setAttribute(attr_name, value)
		self.save_xml_file(self.configxml, self.configdoc)
	
	def get_build_lock(self):
		if self.get_build_attribute("lock", "value") == "1":
			return 1
		elif self.get_build_attribute("lock", "value") == "0":
			return 0
		else:
			return -1
	
	def set_build_lock(self, lock):
		if lock == "1" or lock == 1:
			self.set_build_attribute("lock", "value", "1")
		elif lock == "0" or lock == 0:
			self.set_build_attribute("lock", "value", "0")
		else:
			self.dprint("set build_lock error: " + str(lock))
			return -1
		return 0
	
	def get_force_build_enable(self):
		if self.get_force_build_attribute("enable", "value") == "1":
			return 1
		else:
			return 0
	
	def set_force_build_enable(self, enable):
		if enable == "1" or enable == 1:
			self.set_force_build_attribute("enable", "value", "1")
		elif enable == "0" or enable == 0:
			self.set_force_build_attribute("enable", "value", "0")
		else:
			self.dprint("set force_build_enable error: " + str(enable))
			return -1
		return 0
	
	def get_disable_force_build_after_build(self):
		if self.get_force_build_attribute("disable_after_build", "value") == "1":
			return 1
		else:
			return 0
	
	def get_force_build_projects(self):
		self.configdoc = minidom.parse(self.configxml)
		item = self.configdoc.getElementsByTagName("force_build")
		projects = item[0].getElementsByTagName("proj")
		x = [""]
		ii = 0
		for i in projects:
			x.insert(ii, i.getAttribute("name"))
			ii += 1
		x.remove("")
		return x
	
	def get_built_commit(self, proj_name, branch_name):
		self.buildoc = minidom.parse(self.buildxml)
		log = self.buildoc.getElementsByTagName("log")
		projects = log[0].getElementsByTagName("project")
		for i in projects:
			if i.getAttribute("name") == proj_name:
				branches = i.getElementsByTagName("branch")
				for ii in branches:
					if ii.getAttribute("name") == branch_name:
						return ii.getAttribute("commit")
	
	def update_built_project(self, proj_name, branch_name, commit):
		self.buildoc = minidom.parse(self.buildxml)
		log = self.buildoc.getElementsByTagName("log")
		projects = log[0].getElementsByTagName("project")
		Found = 0
		for i in projects:
			project = i.getAttribute("name")
			if project == proj_name:
				Found = 1
		if Found == 0:
			element = self.buildoc.createElement("project")
			element.setAttribute("name", proj_name)
			log[0].appendChild(element)
			sub_element = self.buildoc.createElement("branch")
			sub_element.setAttribute("name", branch_name)
			sub_element.setAttribute("commit", commit)
			element.appendChild(sub_element)
	
		for i in projects:
			project = i.getAttribute("name")
			if project == proj_name:
				branches = i.getElementsByTagName("branch")
				Found = 0
				for ii in branches:
					if ii.getAttribute("name") == branch_name:
						ii.setAttribute("commit", commit)
						Found = 1
				if Found == 0:
					element = build_doc.createElement("branch")
					element.setAttribute("name", branch_name)
					element.setAttribute("commit", commit)
					i.appendChild(element)
	
		self.save_xml_file(self.buildxml, self.buildoc)
	
	def get_emails(self):
		self.configdoc = minidom.parse(self.configxml)
		users = self.configdoc.getElementsByTagName("user")
		x = [""]
		ii = 0
		for i in users:
			x.insert(ii, i.getAttribute("email"))
			ii += 1
		return x
	
	def send_email(self, subject, content):
		email_list = self.get_emails()
		email_list.remove("")
		msg = MIMEText(content)
		msg['Subject'] = subject
		msg['From'] = "builder"
		msg['To'] = ";".join(email_list)
		try:
			s = smtplib.SMTP()
			s.connect(self.smtp_ipaddr)
			s.sendmail("builder", email_list, msg.as_string())
			s.close()
			return 0
		except Exception, e:
		 	print str(e)
		 	return -1
	

	def get_projects(self):
		self.configdoc = minidom.parse(self.configxml)
		projects = self.configdoc.getElementsByTagName("project")
		proj_info = [""]
		ii = 0
		for i in projects:
			if i.getAttribute("build") == "1":
				proj_info.insert(ii, i.getAttribute("name"))
				ii += 1
		proj_info.remove("")
		return proj_info

	def get_project_info(self, proj_name):
		self.configdoc = minidom.parse(self.configxml)
		projects = self.configdoc.getElementsByTagName("project")
		for i in projects:
			if proj_name == i.getAttribute("name"):
				x = [""]
				x.insert(0, proj_name)
				path = i.getElementsByTagName("path")
				x.append(path[0].getAttribute("value"))
				items = i.getElementsByTagName("branch")
				for ii in items:
					if ii.getAttribute("build") == "1":
						x.append(ii.getAttribute("name"))
				x.remove("")
				return x
		return -1

	def get_result_path(self):
		self.configdoc = minidom.parse(self.configxml)
		items = self.configdoc.getElementsByTagName("result")
		return items[0].getAttribute("path")


class git_handler:
	def __init__(self):
		self.commit = ""
		self.author = ""
		self.merge = ""
		self.commit_date = ""
		self.description = ""
		self.pull_cmd = "git pull"
		self.fetch_cmd = "git fetch"

	def dprint(self, msg):
		print "GIT: " + msg

	def __seek_log_for(self, input, match):	
		input_list = input.split("\n", )
		for i in range(input_list.__len__()):
			tmp_list = input_list[i].split()
			if tmp_list.__len__() > 1:
				if match in tmp_list[0]:
					ret = ""
					for i in range(1, tmp_list.__len__()):
						ret += tmp_list[i]
						ret += " "
					return ret
		return ""

	def __seek_log_for_description(self, input):
		input_list = input.split("\n", )
		index = 0
		for i in range(input_list.__len__()):
			tmp_list = input_list[i].split()
			if tmp_list.__len__() > 1:
				if "Date" in tmp_list[0]:
					index = i +1
		ret = ""
		for i in range(index, input_list.__len__()):
			ret += input_list[i]
			ret += "\n"
		ret = ret.replace('"', '\'')
		return ret

	def parse_log(self, input):
		self.commit = self.__seek_log_for(input, "commit")
		self.merge = self.__seek_log_for(input, "Merge:")
		self.author = self.__seek_log_for(input, "Author:")
		tmp_list = self.author.split("<")
		self.author = tmp_list[0]
		self.commit_date = self.__seek_log_for(input, "Date:")
		self.description = self.__seek_log_for_description(input)
		if self.commit == "" or self.author == "" or self.commit_date == "":
			print "The git log has error!"
			return -1
		else:
			return 0

	def get_log(self):
		stat, log = commands.getstatusoutput("git log -1")
		return log

	def get_latest_commit(self, path):
		if not os.path.exists(path):
			self.dprint(path + " doesn't exist")
			return -1
		os.chdir(path)
		stat, log = commands.getstatusoutput(self.fetch_cmd)	
		stat, log = commands.getstatusoutput(self.pull_cmd)	
		return log
	
	def update_commit_info(self, path):
		if not os.path.exists(path):
			self.dprint(path + " doesn't exist")
			return -1
		os.chdir(path)
		return self.parse_log(self.get_log())

	def reset(self, path):
		if not os.path.exists(path):
			self.dprint(path + " doesn't exist")
			return -1
		os.chdir(path)
		stat, ret = commands.getstatusoutput("git reset --hard")
		return ret
	
	def start(self, path):
		result = 0
		ret = self.reset(path)
		if ret == -1:
			result = -1
		ret = self.get_latest_commit(path)
		if ret == -1:
			result = -1
		ret = self.update_commit_info(path)
		if ret == -1:
			result = -1
		return result

class builder:
	def dprint(self, msg):
		print "BUILDER: " + msg

	def __init__(self):
		'''
		### DON'T MODIFY FILENAME!!!
		builder.sh:		the script to build the branch
		builder_file.list:	includes the filenames which we want to backup with
		error.log:		the log file which we can check if there are build errors within
		'''
		self.builder_sh = "./builder.sh"
		self.builder_file = "./builder_file.list"
		self.error_log = "./error.log"

		### change patter according to project
		#self.error_pattern = ["ERROR:", "ERROR "]

	def __check_env(self, path):
		if not os.path.exists(path):
			self.dprint(path + " doesn't exist")
			return -1
		os.chdir(path)
		if not os.path.exists(self.builder_sh):
			self.dprint("build.sh doesn't exist")
			return -1
		if not os.path.exists(self.builder_file):
			self.dprint("no file list for backup result")
			return -1
		return 0

	def __check_build_error(self, files):
		for i in files:
			if not os.path.exists(i):
				return -1
		'''
		if not os.path.exists(self.error_log):
			return -1
		ret = -1
		for line in open(self.error_log, 'r'):
			tmp = line.upper()
			for i in self.error_pattern:
				ret = tmp.rfind(i)
				if ret != -1:
					return -1
		'''
		return 0

	def get_built_filename(self):
		x = ['']
		for line in open(self.builder_file, 'r'):
			line = line.split('\n')
			x.append(line[0])
		x.remove("")
		return x


	def start(self, path, files):
		if self.__check_env(path) == -1:
			return -2
		stat, ret = commands.getstatusoutput(self.builder_sh)
		return self.__check_build_error(files)

class database:
	def dprint(self, msg):
		print "DATABASE: " + msg

	def __init__(self):
		self.host = "localhost"
		self.user = "root"
		self.passwd = "androidqwerty"
		self.dbname = "buildb"
		self.default_structure = "(date datetime, author varchar(24), pass tinyint(4),\
					commit varchar(48), folder varchar(128),\
					description varchar(512), buildtime varchar(64))"
		try:
			self.conn = MySQLdb.connect(host=self.host, user=self.user, passwd=self.passwd, db=self.dbname)
			self.cursor = self.conn.cursor()	
		except Exception, e:
			self.dprint(str(e))

	def __del__(self):
		self.cursor.close()
		self.conn.close()

	'''
		table name would be "project_name" + "_" + "branch_name"
		+-------------+--------------+------+-----+---------+-------+
		| Field       | Type         | Null | Key | Default | Extra |
		+-------------+--------------+------+-----+---------+-------+
		| date        | datetime     | YES  |     | NULL    |       |
		| author      | varchar(24)  | YES  |     | NULL    |       |
		| pass        | tinyint(4)   | YES  |     | NULL    |       |
		| commit      | varchar(48)  | YES  |     | NULL    |       |
		| folder      | varchar(128) | YES  |     | NULL    |       |
		| description | varchar(512) | YES  |     | NULL    |       |
		| buildtime   | varchar(64)  | YES  |     | NULL    |       |
		+-------------+--------------+------+-----+---------+-------+
	'''
	def create_table(self, table_name):
		if table_name.__len__() > 255:
			self.dprint("length of table name exceeds 255 bytes")
			return -1
		cmd = "create table " + table_name + self.default_structure
		self.cursor.execute(cmd)
		return 0

	def update(self, table, time, author, ispass, commit, folder, des, btime):
		try:
			if time - datetime.datetime.now() > datetime.timedelta(days = 1):
				self.dprint("invalid time for update database!")
				return -1
				'''
			if btime - datetime.datetime.now() > datetime.timedelta(days = 1):
				self.dprint("invalid time for update database!")
				return -1
				'''
		except Exception, e:
		  	self.dprint(str(e))
		  	return -1
		if ispass > 2 or ispass < -1:
		  	self.dprint("value of pass field is out of range.")
		  	return -1
		if folder.__len__() > 128:
		  	self.dprint("length of folder name is out of range.")
		  	return -1

	  	author = author[:24]
	  	commit = commit[:40]
	  	des = des[:512]
		des.replace("\"", "\'")

		cmd = "insert into " + table + " values (\"" + str(time) + "\", \"" + author + "\", \"" +\
		       str(ispass) + "\", \"" + commit + "\", \"" + folder + "\", \"" + des + "\", \"" + str(btime) + "\")"
		try:
			self.cursor.execute(cmd)
		except Exception, e:
			self.dprint(str(e))
			if str(e).rfind("doesn't exist"):
				if self.create_table(table) == -1:
					return -1
				self.update(table, time, author, ispass, commit, folder, des, btime)
		return 0


