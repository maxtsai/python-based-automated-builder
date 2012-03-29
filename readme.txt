Builder configuration
	Max Tsai@2010/5/17

# Create Project
	Create TEST, for example
	$ cd /home/builder/builder/projects
	$ mkdir TEST
	$ cd TEST

# Prepare "builder.sh" & "builder_file.list" per project.
	builder.sh:		the script to build your source code
	builder_file.list:	builder generates ZIP file according to the list.
			Please notice, builder considers this building fail, if 
			(and only if) one of the list doesn't exist.

# Notification email list
	Add user email address into config.xml
