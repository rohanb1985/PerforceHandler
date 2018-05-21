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
configFile ="config\config.yml"
if not os.path.isfile(configFile) :
	exit("No Config file found")	

#load config
with open(configFile) as file:
	userConfigurationMap = yaml.safe_load(file)
	print ("Configuration: " + str(userConfigurationMap))

p4user = sys.argv[1]
p4host = sys.argv[2]

#print ("Connecting to perforce...")
pu = PerforceUtils(p4host = p4host, p4user = p4user, ipIsLogOn = userConfigurationMap['logging'])
p4 = pu.connectToPerforce()
#print ("Connected to perforce.")

ipChangeList = sys.argv[3]
#print ("Fetch details of Change list: " + ipChangeList)
changeListDetails = pu.fetchDetailsOfChangeList(ipChangeList)

submittedChangeLists = list()
submittedChangeLists.append(changeListDetails)

#print ("Calling Merge...")
p4Merge = PerforceMerge(p4, submittedChangeLists, userConfigurationMap)
newlyCreatedChangeLists = p4Merge.mergeAndResolveChangeLists()

if newlyCreatedChangeLists is not None and len(newlyCreatedChangeLists) > 0:
	print("~~~~~~~~~~~~~~Following are the Newly Created Change Lists...~~~~~~~~~~~~~")
	pprint.pprint(newlyCreatedChangeLists)
else:
	print("Nothing to Merge!!")

print ("Completed at: "+str(datetime.datetime.now()))

pu.disconnectFromPerforce()