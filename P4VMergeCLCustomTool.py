from perforce.PerforceUtils import PerforceUtils
from perforce.PerforceMerge import PerforceMerge
import datetime
import yaml
import os
import sys
import pprint

print ("Starting Merge at: "  +str(datetime.datetime.now()))

#fetchConfig
userConfigurationMap = list()
home = os.path.expanduser("~")
configFile ="config\config.yml"
if not os.path.isfile(configFile) :
	exit("No Config file found")	

#load config
with open(configFile) as file:
	userConfigurationMap = yaml.safe_load(file)
	print ("Configuration: " + str(userConfigurationMap))

startDate = datetime.datetime.now().strftime("%Y/%m/%d")
if 'StartDate' in userConfigurationMap.keys():
	startDate = userConfigurationMap['StartDate']
	print ("Start Date %s date found in config" % startDate)
else:
	print ("No config found for start date. Taking current date - %s - as start date" % startDate)

p4user = sys.argv[1]
p4host = sys.argv[2]

pu = PerforceUtils(p4host = p4host, p4user = p4user)
p4 = pu.connectToPerforce()

submittedChangeLists = pu.fetchSubmittedChangeListsFromIpDateToNow(startDate)

p4Merge = PerforceMerge(p4, submittedChangeLists, userConfigurationMap)
newlyCreatedChangeLists = p4Merge.mergeAndResolveChangeLists()

if newlyCreatedChangeLists is not None and len(newlyCreatedChangeLists) > 0:
	print("~~~~~~~~~~~~~~Following are the Newly Created Change Lists...~~~~~~~~~~~~~")
	pprint.pprint(newlyCreatedChangeLists)
else:
	print("Nothing to Merge!!")


print ("Completed at: "+str(datetime.datetime.now()))

pu.disconnectFromPerforce()