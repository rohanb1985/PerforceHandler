from P4 import P4,P4Exception
from utils.MyLogger import MyLogger
import os
import pprint
import datetime

class PerforceUtils:

	def __init__(self, **args):
		if args.get('p4host') is None and args.get('ipP4') is None:
			exit ("Either of P4 Host or the P4 object should be sent!")
		
		if args.get("p4host") is not None:
			self.p4 = P4()
			self.p4.port = args.get("p4host")
			self.p4.user = args.get("p4user")
		elif args.get("ipP4") is not None:
			self.p4 = args.get("ipP4")
			
		if args.get("ipIsLogOn") is not None:
			self.log = MyLogger(args.get("ipIsLogOn"))
		else:
			self.log = MyLogger("N")
			

	def connectToPerforce(self):
		self.log.myPrint ("---> connectToPerforce")
		try:
			self.p4.connect()
			self.log.myPrint ("<--- connectToPerforce")
			return self.p4
		except P4Exception as p4exp:
			self.log.myPrint ("Some P4 exception while logging into to Perforce!")
			exit (p4exp)
		except Exception as exp:
			self.log.myPrint ("Some exception while connecting to Perforce!")
			exit (exp)

	def connectToClient(self, client = ""):
		self.log.myPrint ("--->connectToClient "+client)
		self.p4.client = client
		
	def fetchSubmittedChangeListsFromIpDateToNow(self, startDate):
		try:
			self.log.myPrint ("---> fetchSubmittedChangeListsFromIpDateToNow")
			submittedChangeLists = self.p4.run("changes", "-s", "submitted", "-u", self.p4.user, "@"+startDate+",@now")
			self.log.myPrint ("Changelists fetched: ")
			self.log.myPrint(submittedChangeLists, True)
			self.log.myPrint ("<--- fetchSubmittedChangeListsFromIpDateToNow")
			return submittedChangeLists
		except P4Exception as err:
			self.log.myPrint (err)
			
	def fetchSubmittedChangeListsForBranch(self, ipBranch, startDate, endDate):
		try:
			submittedChangeLists = self.p4.run("changes", "-s", "submitted", "-l", ipBranch+"...@"+startDate+",@"+endDate)
			return submittedChangeLists
		except P4Exception as err:
			self.log.myPrint (err)
		
	def createChangelist(self, desc = "Merge files"):
		try:
			self.log.myPrint ("--->createChangelist")
			changeList = self.p4.fetch_change()
			changeList[ "Description" ] = desc
			createdCLNumber = self.p4.save_change( changeList )[0].split()[1]		
			self.log.myPrint ("<---createChangelist. Changelist created - "+createdCLNumber)
			return createdCLNumber
		except P4Exception as err:
			self.log.myPrint (err)

	def mergeChangelist(self, parentCL, createdCL, fromBranch, toBranch):
		try:
			self.log.myPrint ("--->mergeChangelist parentCL %s, createdCl %s, fromBranch %s, toBranch %s" % (parentCL, createdCL, fromBranch, toBranch))
			
			mergeResults = self.p4.run("merge", "-c", createdCL, "-S", fromBranch, "-P", toBranch, "-s", fromBranch +"/...@"+parentCL+",@"+parentCL)
			self.log.myPrint ("~~~~~~~~~~Merge Results: ~~~~~~~~~~~~" )
			self.log.myPrint(mergeResults, True)
			self.log.myPrint ("<---mergeChangelist")
		except P4Exception as err:
			self.log.myPrint (err)
			
	def deleteChangelist(self, changeListNumber):
		try:
			self.log.myPrint ("---> deleteChangelist")
			deleteResult = self.p4.run("change", "-d", changeListNumber)
			self.log.myPrint ("DeleteResult: "+str(deleteResult))
		except P4Exception as err:
			self.log.myPrint (err)
		
		
	def resolveChangelists(self, client):
		self.log.myPrint ("--->resolveChangelists")
		try:			
			resolveResults = self.p4.run_resolve ( "-am" )
			self.log.myPrint ("~~~~~~~~~~Resolve Results:~~~~~~~~~~~ ")
			self.log.myPrint(resolveResults)
			self.log.myPrint ("<---resolveChangelists")
			return resolveResults
		except P4Exception as err:
			self.log.myPrint (err)
		
	def fetchUserClientForBranch(self, ipBranch):
		try:
			self.log.myPrint ("--->fetchUserClientForBranch for Branch " + ipBranch)
			allClients = self.p4.run("clients", "-u", self.p4.user, "-S", ipBranch)
			self.log.myPrint(allClients, True)
			if allClients is None or len(allClients) <= 0:
				return None;
			systemHost = os.environ['COMPUTERNAME']
			for client in allClients:
				clientHost = client['Host']
				if clientHost == systemHost:
					selectedClientName = client['client']
					self.log.myPrint ("<---fetchUserClientForBranch with Client " + selectedClientName)
					return selectedClientName
			return None;
		except P4Exception as err:
			self.log.myPrint (err)
			
	def fetchDetailsOfChangeList(self, changeListNumber):
		try:
			changeListDetails = self.p4.run("describe","-s", changeListNumber)
			changeListDesc = changeListDetails[0]
			return changeListDesc
		except P4Exception as err:
			self.log.myPrint (err)

	def disconnectFromPerforce(self):
		try:
			self.p4.disconnect()
			self.log.myPrint ("Disconnected.")
		except P4Exception as err:
			self.log.myPrint (err)
			
	def logoutFromPerforce(self):
		try:
			self.p4.run_logout()
			self.log.myPrint ("Logged Out.")
		except P4Exception as err:
			self.log.myPrint (err)
			
	def createNewClient(self, ipBranch, ipStream, ipRoot):
		self.log.myPrint ("--->Creating client for Branch %s, Stream %s, and Root %s" % (ipBranch, ipStream, ipRoot))
		try:
			clientName = os.environ['COMPUTERNAME'] + "_" + ipBranch
			client = self.p4.fetch_client(clientName)
			client["Root"] = ipRoot + ipBranch
			client['Stream'] = ipStream
			client["View"] = [ipStream + "/... //%s/... " % client['Client']]
			client['LineEnd'] = "unix"
			self.p4.save_client(client)
			self.log.myPrint(client, True)
			self.log.myPrint ("<--- Created above Client.")
			return client['Client']
		except P4Exception as err:
			self.log.myPrint (err)
			return None
			
	def fetchClientDetails(self, ipClient):
		try:
			self.log.myPrint ("--->fetchClientDetails for Client " + ipClient)
			clientDetails = self.p4.run("client", "-o", ipClient)
			self.log.myPrint(clientDetails, True)
			self.log.myPrint ("<---fetchClientDetails")
			return clientDetails
		except P4Exception as err:
			self.log.myPrint (err)