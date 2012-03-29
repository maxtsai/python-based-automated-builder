#! /usr/bin/env python
'''
Copyright (c) 2012 Max Tsai<haiching.tsai@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

	The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''


import datetime
import time
import commands
import os
from utils import *

builder_url = "http://172.16.18.85/cgi-bin/index"

class main_builder:
	def dprint(self, msg):
		print str(datetime.datetime.now()) + "\t"+ msg

	def __force_build_wait(self):
		self.dprint("wait for build lock release")
		time.sleep(self.force_wait_time)
		if self.c.get_build_lock() == 1:
			self.__force_build_wait()
	
	def __backup(self, folder, file_list, _pass, branch):
		if not os.path.exists(folder):
			cmd = "mkdir " + folder
			stat, ret = commands.getstatusoutput(cmd)
			if not os.path.exists(folder):
				self.dprint(ret)
				return -1
		files = ['']
		for i in file_list:
		  	if _pass < 1 and not i[i.__len__()-4:i.__len__()] == ".log":
		  		continue
			cmd = "cp " + i + " " + folder
			stat, ret = commands.getstatusoutput(cmd)	
		  	files.append(i)

		### tar all files per branch
		cmd = ""
		for i in files:
			ii = i.split("/")
			cmd += ii[ii.__len__()-1] 
			cmd += " "
		cmd = "tar zcvf " + branch + ".tgz " + cmd
		stat, org_path = commands.getstatusoutput("pwd")
		os.chdir(folder)
		stat, log = commands.getstatusoutput(cmd)

		### remove all files except *error.log & *.tgz
		cmd = ""
		for i in files:
			ii = i.split("/")
			ii = ii[ii.__len__()-1]
			if not ii == branch + "_error.log":
				cmd += ii
				cmd += " "
		cmd = "rm " + cmd	
		stat, log = commands.getstatusoutput(cmd)

		os.chdir(org_path)


	def __build_branch(self, project, branch, path):

		self.g.start(path)

		if self.c.get_force_build_enable() == 0:
			if self.g.commit[:40] == self.c.get_built_commit(project, branch)[:40]:
				self.dprint(project + "/" + branch + ": up-to-date. no build.")
				return 0
			self.dprint(project + "/" + branch + ": start build (" + self.g.commit[:20] + " != "\
				       	+ self.c.get_built_commit(project, branch)[:20] + ")")
		else:
			self.dprint(project + "/" + branch + ": start force build (" + self.g.commit[:20] + " <-> "\
				       	+ self.c.get_built_commit(project, branch)[:20] + ")")

		ret_file_list = self.b.get_built_filename()
		for i in range(ret_file_list.count("")):
			ret_file_list.remove("")

		start_time = datetime.datetime.now()
		_pass = self.b.start(path, ret_file_list)
		end_time = datetime.datetime.now()

		if _pass == -2:
			self.dprint(project + "/" + branch + ": env config error. no build")
			return -1
		_pass += 1

		ret_folder = self.start_time.strftime('%Y%m%d-%H%M%S') + "_" + project

		### backup files
		if not os.path.exists(self.c.get_result_path()):
			cmd = "mkdir " + self.c.get_result_path()
			stat, ret = commands.getstatusoutput("mkdir " + self.c.get_result_path())
			if not os.path.exists(self.c.get_result_path()):
				self.dprint(ret)
				return -1
		ret = self.__backup(self.c.get_result_path() + ret_folder, ret_file_list, _pass, branch)
		if ret == -1:
		  	self.dprint(project + "/" + branch + ": backup files error")
		  	return -1

		### table of database: project-name_branch-name
		ret = self.d.update(project + "_" + branch, self.start_time, self.g.author, _pass, self.g.commit, \
				ret_folder, self.g.description, end_time - start_time)
		if ret == -1:
			cmd = "rm -rf " + self.c.get_result_path() + ret_folder
			stat, ret = commands.getstatusoutput(cmd)
			self.dprint("update database table: \'" + project + "_" + branch + "\' error")
			return -1

		self.c.update_built_project(project, branch, self.g.commit)

		### send emails, if build break
		if _pass < 1:
			self.dprint(project+"/"+branch+": build break")
			self.c.send_email("[build break alert] " + project + "/" + branch + "#  author:" + self.g.author +\
					", commit:" + self.g.commit[:10], "Please check " + builder_url + "?page=1&table="+\
				       	project + "_" + branch)
		else:
			self.dprint(project+"/"+branch+": build pass")


	def __build_project(self, proj_info):
		if proj_info.__len__() < 3:
			self.dprint("project: " + proj_info[0] +" information error")
			return -1
		self.start_time = datetime.datetime.now()
		for i in proj_info[2:]:
			self.__build_branch(proj_info[0], i, proj_info[1] + "/" + i)

			######################
			### make boot.img  ###
			######################

	
	def __build(self):
		if self.c.get_force_build_enable() == 1:
			self.projects = self.c.get_force_build_projects()
		else:
			self.projects = self.c.get_projects()

		if self.projects.__len__() < 1:
			self.dprint("no project exists.")
			return -1
		
		for i in self.projects:
			proj_info = self.c.get_project_info(i)
			if proj_info == -1:
				self.dprint("project: " + i + " doesn't exist.")
				continue
			ret = self.__build_project(proj_info)
		
		if self.c.get_disable_force_build_after_build() == 1:
			self.c.set_force_build_enable(0)


	def __init__(self):
		self.c = config()
		self.b = builder()
		self.g = git_handler()
		self.d = database()
		self.force_wait_time = 60 #seconds
		self.projects = ['']
		self.start_time = ""

		if self.c.get_build_lock() == 1 and self.c.get_force_build_enable() == 1:
			self.__force_build_wait()

		if self.c.get_build_lock() == 1:
			self.dprint("Under building, stop this action.")
			return

		if self.c.get_build_lock() == 0:
			self.c.set_build_lock(1)
			self.__build()
		else:
			self.dprint("Why build lock is kept?")

	def __del__(self):
		self.c.set_build_lock(0)
		pass

os.chdir("/home/builder/builder")
m = main_builder()




