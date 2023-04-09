from __future__ import print_function
import datetime
import json
import time
from json import JSONDecodeError
import requests
import boto3
import xlrd
from mapxls import MAP_DATE_XLS
import os
import isengard
from requests_aws4auth import AWS4Auth
import urllib3


# Rotation IDs
<redacted>

# Oncall auth variables

ONCALL_REGION = 'us-west-2'
ONCALL_SERVICE = 'oncall-api'
ONCALL_HOST = '<redacted>'
URL_ONCALL = '<redacted>'
ONCALL_HEADERS = {'content-type': 'application/json', 'host': ONCALL_HOST}

# Team aliases - can be found in on call web page
TEAM_ALIAS = ['aws-ams-ops-oncall',
              'aws-ams-ops-corp-oncall',
              'aws-ams-ops-eps',
              'aws-ams-patch-oncall'
              ]

ONCALL_TEAM_DICT = {'aws-ams-ops-oncall': 'Ops Primary: ', 
                    'aws-ams-ops-corp-oncall': 'CORP Oncall: ',
                    'aws-ams-patch-oncall': 'Patch Primary: ',
                    'aws-ams-ops-eps': 'EPS On Call: '
                    }

fakelist =  [<redacted>] 

IAD_Roster = "<redacted>"

<internal AUTH process redacted>

S3_CLIENT = boto3.client("s3")
Filename = 'IAD_DFW_SEA_2022-Schedule.xlsx'
FilePath = "/tmp/" + Filename
S3_CLIENT.download_file('iad-sch', Filename, FilePath)
SCHEDULE_LOCATION = FilePath
WB = xlrd.open_workbook(SCHEDULE_LOCATION)
SHEET = WB.sheet_by_index(0)
DAY_NUMBER = 1



def get_primary_from_oncall(next_date, oncall_team):
    # 'aws-ams-ops-oncall', 'aws-ams-rfc-primary', 'aws-ams-sr-primary', 'aws-ams-alerts-oncall'
    # aws-ams-patch-oncall, aws-ams-ops-eps
    url = "<redacted>
    print(url)
    response = requests.get(url, headers=ONCALL_HEADERS, auth=AUTH)
    print(response.status_code)
    """
    NOTE - Please add engineers accordingly as they get onboarded in the below on_call list
    """
    print(response)
    print(type(response))
    len_on_call_members = len(response.json()[0])
    print(len_on_call_members)
    for num in range(len_on_call_members):
        try:
            engineer = response.json()[num]['oncallMember'][0]
            if engineer in fakelist:
                # print(engineer)
                return engineer
        except IndexError:
            continue


def get_next_day_assignments():
        """
        This method will POST IAD Ops On Call schedule for the immediate next day using Chime Webhook
        """
        day_start = 1
        day_end = 2
        for value in range(day_start, day_end):
                next_date = datetime.date.today() + datetime.timedelta(days=value)
                print(next_date)
                
                for oncall_team in TEAM_ALIAS:
                        primary = get_primary_from_oncall(next_date, oncall_team)
                        schedule_next_day += ONCALL_TEAM_DICT[oncall_team] + "@" + str(primary) + "\n"
                message = "###################################################################################\n" \
                    + "\n**IAD schedule for " + str(next_date) + " Take 1 - \n\n" + schedule_next_day.strip() \
                    + "\n###################################################################################"
                
                iad_helpers,sea_helpers,dfw_helpers,mex_helpers,iad_nonhelpers,dfw_nonhelpers,mex_nonhelpers = get_helpers(str(next_date))

                bold1 = "IAD DFW and SEA Helpers for " + str(next_date) 
                bold2 = "Tomorrow's primaries! " 
                msg = "IAD Engineers in Traning from 09:00-15:00 EST\n" + str(iad_nonhelpers) + "\n\n" \
                + "IAD Engineers from 09:00-17:00 EST\n" + str(iad_helpers) + "\n\n" \
                + "DFW Engineers in Training from 10:00-15:00 EST\n" + str(dfw_nonhelpers) + "\n\n" \
                + "DFW Engineers from 10:00-18:00 EST\n" + str(dfw_helpers) + "\n\n" \
                + "MEX Engineers in Training from 10:00-15:00 EST\n" + str(mex_nonhelpers) + "\n\n" \
                + "MEX Engineers from 10:00-18:00 EST\n" + str(mex_helpers) + "\n\n" \
                + "SEA Engineers who can help IAD/DFW from 12:00-15:00 EST \n" + str(sea_helpers)                
                print(msg)
                requests.post(url=IAD_Roster, json={"bold1": bold1,"bold2": bold2,"content1": msg, "content2": message})
                
        return None


def get_helpers(*month_date):
        """
        This method is used to find engineers available to work in a given day
        USAGE -
        get_engineer_spreadsheet('2021-06-06') will return engineer aliases available on June 6, 2021
        """
        print(f'within get helperfn : {month_date}')
        engineer_count = 99
        # Row number of engineer's alias in Excel sheet
        # New spreadsheet row value for engineer alias is 0
        engineer_alias_xls = 0
        for dt in month_date:
                # on_call_engineers = []
                iad_helpers = []
                sea_helpers = []
                dfw_helpers = []
                mex_helpers = []
                dfw_nonhelpers = []
                iad_nonhelpers = []
                mex_nonhelpers = []
                print(MAP_DATE_XLS)
                print(dt)
                value = MAP_DATE_XLS[dt]
                
                for engineer_names in range(0, engineer_count):
                        # Get value of date's cell value from spreadsheet
                        # Get time slot rows
                        # Use this to determine who is available for a given day's schedule
                        print(f'SheetRowValues {SHEET.row_values(value)}')
                        time_slots = SHEET.row_values(value)[1:100]
                        # print(f'SheetRowValues {time_slots}')
                        # Check if time slot cell value is not empty & not night shift (11:00 PM to 7:00 AM)
                        if time_slots[engineer_names] != '' and time_slots[engineer_names] != 'US SOIL' and \
                                        time_slots[engineer_names] != 'PROJECT' and time_slots[engineer_names] != 'PTO' and \
                                        time_slots[engineer_names] != 'COMP DAY'and time_slots[engineer_names] != 'NHT' and \
                                        time_slots[engineer_names] != 'NIGHTS' and time_slots[engineer_names] != 'Training + 12-5':
                                # Get 7:00 AM to 3:00 PM and 9:00 AM to 5:00 PM cell values
                                if time_slots[engineer_names] == '09:00-17:00':
                                        val = SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                                        iad_helpers.append("@" + val)
                                elif time_slots[engineer_names] == '12:00-20:00':
                                        val = SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                                        sea_helpers.append("@" + val)
                                elif time_slots[engineer_names] == '12:00-20:00 (MEX)':
                                        val = SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                                        sea_helpers.append("@" + val)
                                elif time_slots[engineer_names] == '10:00-18:00' :
                                        val = SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                                        dfw_helpers.append("@" + val)
                                elif time_slots[engineer_names] == '10:00-18:00 (MEX)' :
                                        val = SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                                        mex_helpers.append("@" + val)
                                elif time_slots[engineer_names] == '07:00-12:00 + Training' or time_slots[engineer_names] == '10:30-3:30 + Training' or  time_slots[engineer_names] == '09:30-02:00 + Training' or time_slots[engineer_names] == '07:00-15:00':                    
                                        val = SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                                        iad_nonhelpers.append("@" + val)
                                elif time_slots[engineer_names] == '10:00-15:00 + Training' :
                                        val = SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                                        dfw_nonhelpers.append("@" + val)
                                elif time_slots[engineer_names] == '10:00-15:00 + Training (MEX)' :
                                        val = SHEET.cell_value(engineer_alias_xls, engineer_names + 1)
                                        mex_nonhelpers.append("@" + val)
                                        

                    

                # print("Available engineers for " + dt + " - " + str(on_call_engineers) + "\n")
        return iad_helpers,sea_helpers,dfw_helpers,mex_helpers,iad_nonhelpers,dfw_nonhelpers,mex_nonhelpers


def lambda_handler(event,context):
        get_next_day_assignments()
        
    

