#!/bin/sh
###########################################
####  v2v project install shell file    ###
####  2016/1/14                         ###
###########################################

#v2v api service IP
API_SERVICE_IP=162.3.202.50
API_SERVICE_PORT=9999


#keystone connect info
AUTH_URL_IP=identity.cloud.hybrid.huawei.com
AUTH_URL_PORT=443
AUTH_ADMIN_USER=birdie
AUTH_ADMIN_PASSWD=N8296FGj0gDK1OA8djBQ50u/7CZvJ+RfE2qNhiGICE8=


#v2v api service name
API_SERVICE_NAME=birdie-api
#v2v api service register user name
API_REGISTER_USER_NAME=birdie
#v2v api service register user password
API_REGISTER_USER_PASSWD=Huawei123
#v2v api register relation role name
API_REGISTER_ROLE_NAME=admin
#v2v api register relation tenant name
API_REGISTER_TENANT_NAME=service
#v2v api service register service name
API_REGISTER_SERVICE_NAME=birdie
#v2v api service register service type
API_REGISTER_SERVICE_TYPE=birdie


#source code file directory
CODE_DIR=/usr/local/lib64/python2.6/site-packages/
CONFIG_DIR=/etc/birdie
BIN_DIR=/usr/bin
API_CONFIG_FILE=hybrid-v2v.conf
PROJECT_NAME=birdie

#CONSISTENT VARIABLE VALUE
LOG_DIR=/var/log/birdie
LOG_FILE=${LOG_DIR}/install.log
TIME_CMD=`date '+%Y-%m-%d %H:%M:%S'`
BOOL_TRUE_INT=0
BOOL_FALSE_INT=1
ERROR_INT=2

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

#####################################################################
# Function: system_check
# Description: v2v service relies openstack(keystone), so system must
#               install openstack first.
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
system_check()
{
   keystoneservice=${keystone service-list | awk '/ keystone / {print $2}'}
   if [ $? -ng 0 ]; then
      #log error
      return 1
   fi
   
   return 0
}

#####################################################################
# Function: check_api_register_user_exist
# Description: check api user info is registered or not
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
check_api_register_user_exist()
{
    user=$(keystone user-list | awk '/ '${API_REGISTER_USER_NAME}' / {print $2}')
	
	if [ $? -ne 0 ]; then
	   echo ${TIME_CMD} "check v2v api register user error." >> "${LOG_FILE}"
	   keystone user-list | awk '/ '${API_REGISTER_USER_NAME}' / {print $2}'  >> "${LOG_FILE}" 2>&1
	   return ${ERROR_INT}
	fi
	
	#check is null
	if [ -z $user ]; then
	    #is null
		echo ${TIME_CMD} "check v2v api register user is null" >> "${LOG_FILE}"
	    return ${BOOL_TRUE_INT}
	else
	    #other
		echo ${TIME_CMD} "check v2v api register user is " "${user}" >> "${LOG_FILE}"
	   return ${BOOL_FALSE_INT}
	fi
}


#####################################################################
# Function: copy_files_to_dir
# Description: copy v2v project files to install directory
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
copy_files_to_dir()
{
    #copy  running file to /usr/bin

    for f in ${API_SERVICE_NAME} ${GATEWAY_SERVICE_NAME}; do
	
	    if [ -f ${BIN_DIR}/$f ]; then
		    rm -f ${BIN_DIR}/$f
		fi
		
        cp $f ${BIN_DIR}
		
		if [ ! -x ${BIN_DIR}/$f ]; then
		  chmod +x ${BIN_DIR}/$f
		fi
		 
    done 

    #copy source code to /usr/local/lib/python2.7/dist-packages
	if [ -d ${CODE_DIR}/${PROJECT_NAME} ]; then
	   rm -rf ${CODE_DIR}/${PROJECT_NAME}
	fi
    cp -r ../${PROJECT_NAME} ${CODE_DIR}

    #make config file directory
	if [ -d ${CONFIG_DIR} ]; then
	   rm -rf ${CONFIG_DIR}
	fi
	
    mkdir ${CONFIG_DIR}

    #copy config file to /etc/birdie
    cp ../etc/${PROJECT_NAME}/* ${CONFIG_DIR}
}

#####################################################################
# Function: register_api_services
# Description: register api services info to keystone
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
register_api_services()
{
    #check user is register or not
	check_api_register_user_exist
	if [ $? -eq ${ERROR_INT} ]; then
	   echo  ${TIME_CMD} "error: v2v api register user" >> "${LOG_FILE}"
	   return ${ERROR_INT}	   
	fi
	if [ $? -eq ${BOOL_TRUE_INT} ]; then
        #register the user of v2v service 
        keystone user-create --name=${API_REGISTER_USER_NAME} --pass=${API_REGISTER_USER_PASSWD} --email=admin@example.com

        #register v2v user and tenant relation (eg: service Tenant / admin Role)
        keystone user-role-add --user=${API_REGISTER_USER_NAME} --tenant=${API_REGISTER_TENANT_NAME} --role=${API_REGISTER_ROLE_NAME}
	else
	   echo  ${TIME_CMD} "warning: v2v api register user exist. there not register. user name: " "${API_REGISTER_USER_NAME}" >> "${LOG_FILE}"
	fi
	
    #register v2v service 
    keystone service-create --name=${API_REGISTER_SERVICE_NAME} --type=${API_REGISTER_SERVICE_TYPE} --description="Hybrid vm manager"

    #register v2v endpoint
	serviceId=$(keystone service-list | awk '/ '${API_REGISTER_SERVICE_NAME}' / {print $2}')
    keystone endpoint-create --region=RegionOne --service-id=${serviceId} \
	--publicurl=http://${API_SERVICE_IP}:${API_SERVICE_PORT}/v1/$\(tenant_id\)s \
	--adminurl=http://${API_SERVICE_IP}:${API_SERVICE_PORT}/v1/$\(tenant_id\)s \
	--internalurl=http://${API_SERVICE_IP}:${API_SERVICE_PORT}/v1/$\(tenant_id\)s >> "${LOG_FILE}" 2>&1
	
	if [ $? -ne 0 ]; then
	   echo "create endpoint failed" >> "${LOG_FILE}"
	   return ${ERROR_INT}
	fi 
}


#####################################################################
# Function: start_api_service
# Description: start api service
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
start_api_service()
{
   ${BIN_DIR}/${API_SERVICE_NAME} --config-file ${CONFIG_DIR}/${API_CONFIG_FILE} & 
   
   if [ $? -ne 0 ]; then
      echo  ${TIME_CMD} "start api service error." >> "${LOG_FILE}"
	  ${BIN_DIR}/${API_SERVICE_NAME} --config-file ${CONFIG_DIR}/${API_CONFIG_FILE} & >> "${LOG_FILE}" 2>&1
   fi
}


#####################################################################
# Function: reset_api_config_file
# Description: reset api service starting config file
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
reset_api_config_file()
{
    #sed -i "s/^osapi_v2v_listen=.*/osapi_v2v_listen=${API_SERVICE_IP}/g"
    #reset v2v api config info
	sed -i "s:#OSAPI_V2V_LISTEN_IP#:${API_SERVICE_IP}:g" ${CONFIG_DIR}/${API_CONFIG_FILE}
	sed -i "s:#OSAPI_V2V_LISTEN_PORT#:${API_SERVICE_PORT}:g" ${CONFIG_DIR}/${API_CONFIG_FILE}
	#reset keystone config info
	sed -i "s:#AUTH_URL_IP#:${AUTH_URL_IP}:g" ${CONFIG_DIR}/${API_CONFIG_FILE}
	sed -i "s:#AUTH_URL_PORT#:${AUTH_URL_PORT}:g" ${CONFIG_DIR}/${API_CONFIG_FILE}
    sed -i "s:#AUTH_USER_NAME#:${AUTH_ADMIN_USER}:g" ${CONFIG_DIR}/${API_CONFIG_FILE}
	sed -i "s:#AUTH_USER_PASSWD#:${AUTH_ADMIN_PASSWD}:g" ${CONFIG_DIR}/${API_CONFIG_FILE}
}



#####################################################################
# Function: main
# Description: main func
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
main()
{
    #check system
	#system_check
	generate_log_file
	copy_files_to_dir

	if [ "$1"x = "v2v-api"x ]; then
	
	   register_api_services
	   
	   reset_api_config_file
	   
	   start_api_service   
	   
	elif [ "$1"x = "v2v-all"x ]; then
	
	   register_api_services
	   
	   reset_api_config_file
	   
	   start_api_service
	    
	else
	   echo "Error input parameter.
	         install <v2v-api or v2v-all>"
		exit 1
    fi	
}

main $@




