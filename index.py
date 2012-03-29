#!/usr/bin/env python
#coding:utf-8

import cgi
import string
from utils import database

d = database()
current_table = "N0B1_uboot"
current_page = 1
num_per_page = 20
result_path = "/result/"


def prepare_html():
	print "Content-Type: text/html"
	print # blank line, end of headers
	print "<html>"
	print "<head>"
	print "<meta http-equiv='Content-Type' content='text/html; charset=utf-8' />"
	print "<title>Builder Report</title>"
	print "</head>"
	print "<body>"
	print "<p align=center><b><font size=5>Builder Report</font></b></p>"

def show_pg_link():
	if not total > num_per_page:
		return

	total_page = total/num_per_page
	if total % num_per_page > 0:
		total_page += 1

	if (current_page - 1 ) < 2:
		print "<a href=?page=1&table=" + current_table + ">prev</a>"
	else:
		print "<a href=?page="+ str(current_page-1) + "&table=" + current_table + ">prev</a>"

	for i in range(total_page+1):
		if i < current_page + 5 and i > current_page - 5 and not i == 0:
			if i == current_page:
				print str(i)
			else:
				print "<a href=?page=" + str(i) + "&table=" + current_table + ">" + str(i) + "</a>"

	if (current_page + 1) * num_per_page > total:
		if total/num_per_page < 1:
			print "<a href=?page=1&table=" + current_table + ">next</a>"
		else:
			if total % num_per_page > 0:
				print "<a href=?page=" + str(total/num_per_page + 1) + "&table=" + current_table + ">next</a>"
			else:
				print "<a href=?page=" + str(total/num_per_page) + "&table=" + current_table + ">next</a>"
	else:
		print "<a href=?page=" + str(current_page+1) + "&table=" + current_table +">next</a>"


def show_pre_table():
	print "<table width=100% border=1 bordercolor=\"#b3b3b3\" cellpadding=3 cellspacing=0>"
	print "<tr valign=top>"
	print "<td><p align=center><b>date</b></p>"
	print "<td><p align=center><b>author</b></p>"
	print "<td><p align=center><b>pass</b></p>"
	print "<td><p align=center><b>commit</b></p>"
	print "<td><p align=center><b>result</b></p>"
	print "<td><p align=center><b>description</b></p>"
	print "<td><p align=center><b>build time</b></p>"
	print "</tr>"

def show_data(input):
	branch = current_table.split("_")
	branch = branch[1]
	if input[2] < 1:
		print "<tr valign=top bgcolor=#ff0000>"
	elif input[2] > 1:
		print "<tr valign=top bgcolor=#00ff00>"
	else:
		print "<tr valign=top>"
	print "<td><p align=center>" + str(input[0]) + "</p>"
	print "<td><p align=center>" + input[1] + "</p>"
	print "<td><p align=center>" + str(input[2]) + "</p>"
	print "<td><p align=center>" + input[3] + "</p>"
	if input[2] < 1:
		print "<td><p align=center>"+"<a href="+result_path+input[4]+"/"+branch+"_error.log>error log</a></p>"
	else:
		print "<td><p align=center>"+"<a href="+result_path+input[4]+"/"+branch+".tgz>image</a></p>"
	desc = input[5]
	print "<td><p align=left width=45%>" + desc + "</p>"
	print "<td><p align=center>" + str(input[6]) + "</p>"
	print "</tr>"


prepare_html()
form=cgi.FieldStorage()
d.cursor.execute("show tables")
tables = d.cursor.fetchall()

if form.has_key('table'):
	current_table = form['table'].value

d.cursor.execute("select count(*) from " + current_table)
((total,),) = d.cursor.fetchall()

if form.has_key('page'):
	current_page = string.atoi(form['page'].value, 10)

print "<form action='index' method='post'>"
print "<select name='table' size=1>"
for i in tables:
	if i[0] == current_table:
		print "<option value='" + i[0] + "' selected >" + i[0] + "</option>"
	else:
		print "<option value='" + i[0] + "' >" + i[0] + "</option>"
print "</select>"
print "<input type=submit value='query'>"
print "<hr>"
print "<p>"
print "<img src=\"/android.gif\" width=\"30\" height=\"30\" alt=\"android.gif\" align=center>"
print "<b>Table = " + current_table  + "</b>"
print "&nbsp"*10
show_pg_link()
tmp = current_table.split('_')
if not tmp[1] == "eclair":
	print "&nbsp"*30
	print "<a href=\"/result/arm-2009q3-67-arm-none-linux-gnueabi-i686-pc-linux-gnu.tar.bz2\">toolchain: 2009q3-67</a>"
	print "&nbsp"*5
	print "<a href=\"/result/arm-2010q1-188-arm-none-eabi-i686-pc-linux-gnu.tar.tar\">toolchain: 2010q1-188</a>"
if tmp[1] == "eclair":
	print "&nbsp"*30
	print "<a href=\"/result/Flash_v10.1.92.8.apk\">Flash_v10.1.92.8</a>"
print "</p>"
print "</form>"

if (current_page - 1 ) < 1:
	cmd = "select * from " + current_table + " order by date desc limit " + \
		str(0) + "," + str(num_per_page)
else:
	cmd = "select * from " + current_table + " order by date desc limit " + \
		str((current_page-1)*num_per_page) + "," + str(num_per_page)

d.cursor.execute(cmd)
rows = d.cursor.fetchall()

show_pre_table()
for i in rows:
	show_data(i)


print "</body>"
