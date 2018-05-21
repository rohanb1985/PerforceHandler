from perforce.PerforceUtils import PerforceUtils
from utils.MyLogger import MyLogger
import yaml
import pprint
import re

class PerforceMerge:

	def __init__(self, ipP4, ipSubmittedChangeLists, ipUserConfigurationMap):
		self.p4 = ipP4
		self.submittedChangeLists = ipSubmittedChangeLists
		self.userConfigurationMap = ipUserConfigurationMap
		self.log = MyLogger(self.userConfigurationMap['logging'])
		
	def getBranchesConfig(self):
		branchesConfig = list()
		self.log.myPrint ("User Configuration: " + str(self.userConfigurationMap))
		branchesFile = self.userConfigurationMap['BranchesFile']
		if branchesFile is None:
			exit ("Branches File missing! Please check configuration")
		with open(branchesFile) as file:
			branchesConfig = yaml.safe_load(file)
			self.log.myPrint ("Branches Config: " + str(branchesConfig))
			if len(branchesConfig) <= 0 :
				exit("Branches configuration not properly defined!")
		return branchesConfig;
		
	def mergeAndResolveChangeLists(self):
		mergeAndResolveResults = list()
		targetBranchClNoDict = dict()

		branchesConfig = self.getBranchesConfig()

		for changeList in self.submittedChangeLists:
			clNumber = changeList['change']
			originalCLBranch = changeList['path'].split(self.userConfigurationMap['p4DepotHead'])[1].split("/")[0]
			print ("Changelist:" + clNumber + "-------- Branch: "+originalCLBranch)
			targetBranches = branchesConfig['BranchDetails'][originalCLBranch]
			if targetBranches is None:
					continue
			for targetBranch in targetBranches:			
				if targetBranch in targetBranchClNoDict:
					targetBranchClNoDict[targetBranch].append(clNumber)
				else:
					targetBranchClNoDict[targetBranch] = list()
					targetBranchClNoDict[targetBranch].append(clNumber)

		self.log.myPrint ("targetBranchClNoDict - " )#+ str(targetBranchClNoDict))
		self.log.myPrint (targetBranchClNoDict, True)

		pu = PerforceUtils(ipP4 = self.p4, ipIsLogOn = self.userConfigurationMap['logging'])
		
		for targetBranchName in targetBranchClNoDict.keys():
			targetBranch = self.userConfigurationMap['p4DepotHead'] + targetBranchName
			self.log.myPrint ("Fetching user's client for input branch - "+targetBranch)
			client = pu.fetchUserClientForBranch(targetBranch)
			if client is None:
				userRoot = self.userConfigurationMap['userRoot']
				client = pu.createNewClient(targetBranchName, targetBranch, userRoot)
				if client is None:
					continue
			self.log.myPrint ("Connecting to perforce with client: "+client)
			pu.connectToClient(client)
			
			newlyCreatedCLList = list()
			for parentChangeList in targetBranchClNoDict[targetBranchName]:
				parentCLDetails = pu.fetchDetailsOfChangeList(parentChangeList)
				self.log.myPrint ("~~~~~~~~~Change Details:~~~~~~~~~~~")
				self.log.myPrint (parentCLDetails, True)
				parentCLDesc = parentCLDetails['desc']
				self.log.myPrint ("Creating a new changelist...")
				createdCLNumber = pu.createChangelist("Merging "+originalCLBranch+" CL "+parentCLDetails['change']+" to "+targetBranchName+" - "+parentCLDesc)
				parentCLBranch = re.match(r'%s([^/]+)' % self.userConfigurationMap['p4DepotHead'], parentCLDetails['path']).group(0)
				self.log.myPrint ("Parent Branch" + str(parentCLBranch))				
				self.log.myPrint ("Merging files...")
				mergeResults = pu.mergeChangelist(parentChangeList, createdCLNumber, parentCLBranch, targetBranch)
				newCLDetails = pu.fetchDetailsOfChangeList(createdCLNumber)
				self.log.myPrint ("New CL Details: "+str(newCLDetails))				
				if 'depotFile' not in newCLDetails.keys():
					pu.deleteChangelist(createdCLNumber)
				else:
					newlyCreatedCLList.append(createdCLNumber)
			
			if len(newlyCreatedCLList) <= 0:
				continue
				
			newlyCreatedCLDict = {"Changelist created for "+client : newlyCreatedCLList}
			mergeAndResolveResults.append(newlyCreatedCLDict)
			
			self.log.myPrint ("Resolving changelists...")
			resolveResults = pu.resolveChangelists(client)
			if resolveResults is not None and len(resolveResults) > 0:
				unresolvedFilesList = list()
				for resolveResult in resolveResults:
					if "resolve skipped" in resolveResult:
						unresolvedFilesList.append(resolveResult)
				if len(unresolvedFilesList) > 0:
					unresolvedFilesDict = {"UnResolved files for "+client : unresolvedFilesList}					
					mergeAndResolveResults.append(unresolvedFilesDict)
			
		return mergeAndResolveResults