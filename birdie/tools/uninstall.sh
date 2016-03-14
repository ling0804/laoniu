#!/bin/sh
###########################################
####  v2v project uninstall shell file  ###
####  2016/1/14                         ###
###########################################

#v2v api service name
API_SERVICE_NAME=birdie
#v2v api service user name
API_REGISTER_USER_NAME=birdie
#v2v api role name
API_REGISTER_ROLE_NAME=admin
#v2v api service register name
API_REGISTER_SERVICE_NAME=birdie
#v2v api register relation tenant name
API_REGISTER_TENANT_NAME=service


#source code file directory
CODE_DIR=/usr/local/lib/python2.7/dist-packages/birdie
CONFIG_DIR=/etc/birdie
BIN_DIR=/usr/bin
LOG_DIR=/var/log/birdie
LOG_FILE=${LOG_DIR}/birdie_uninstall.log
TIME_CMD=`date '+%Y-%m-%d %H:%M:%S'`

#####################################################################
# Function: generate_log_file
# Description: generate log file
# Parameter:
# input:
# $1 -- NA 
# $2 -- NA
# output: NA
# Return:
# RET_OK
# Since: 
#
# Others:NA
#######################################################################
generate_log_file()
{ 
    if [ ! -d ${LOG_DIR} ]; then
	   mkdir -p ${LOG_DIR}
	fi
	
	if [ ! -f ${LOG_FILE} ]; then
	   touch ${LOG_FILE}
	fi
}

#############################################################
# Function: stop_api_service
# Description: stop v2v api service (kill this service process).
# Parameter:
# input:
# $1 -- NA 
# $2 -- NA
# output: NA
# Return:
# RET_OK
# Since: 
#
# Others:NA
#############################################################
stop_service()
{
    ps aux|grep ${API_SERVICE_NAME}|awk '{print $2}'|xargs kill -9
	
	if [ $? -eq 0 ]; then
	   echo  ${TIME_CMD} "stop api service success" >> "${LOG_FILE}"
	else
	  #log error
	  echo  ${TIME_CMD} "stop api service error" >> "${LOG_FILE}"
	fi
}


####################################################################
# Function: clear_files
# Description: clear v2v project files.
# Parameter:
# input:
# $1 -- NA 
# $2 -- NA
# output: NA
# Return:
# RET_OK
# Since: 
#
# Others:NA
#####################################################################
clear_files()
{
    #remove bin file 
    rm -f ${BIN_DIR}/${API_SERVICE_NAME}	
   
	#remove source code files
	rm -rf ${CODE_DIR}
	
	#remove config files
	rm -rf ${CONFIG_DIR}
}

####################################################################
# Function: clean_register_info
# Description: clean v2v project register information in keystone.
# Parameter:
# input:
# $1 -- NA 
# $2 -- NA
# output: NA
# Return:
# RET_OK
# Since: 
#
# Others:NA
#####################################################################
clean_register_info()
{
   #clean api service register info
   keystone user-delete ${API_REGISTER_USER_NAME}
   keystone user-role-remove --user=${API_REGISTER_USER_NAME} --role=${API_REGISTER_ROLE_NAME} --tenant=${API_REGISTER_TENANT_NAME}
   
   #remove endpoint
   api_service_id=$(keystone service-list | awk '/ ${API_REGISTER_SERVICE_NAME} / {print $2}')
   api_endpoint_id=$(keystone endpoint-list | awk '/ $api_service_id / {print $2}')
   keystone endpoint-delete $api_endpoint_id
   
   #remove service
   keystone service-delete ${API_REGISTER_SERVICE_NAME}
}

####################################################################
# Function: main
# Description: main func.
# Parameter:
# input:
# $1 -- NA 
# $2 -- NA
# output: NA
# Return:
# RET_OK
# Since: 
#
# Others:NA
#####################################################################
main()
{
   generate_log_file
   #stop service 
   stop_service
 
   #clear all files
   clear_files
   
   #clean register info in keystone
   clean_register_info
}

main $@


