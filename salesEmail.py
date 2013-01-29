import sys
import csv
import string
from datetime import date
from time import strptime
import datetime
import re
import argparse


def redoDate(date):
	date=strptime(date,"%m/%d/%Y")
	year=date.tm_year
	month=date.tm_mon
	if len(str(month)) != 2:
		month="0"+str(month)
	day=date.tm_mday
	if len(str(day)) != 2:
		day="0"+str(day)
	date=str(year)+str(month)+str(day)
	return date

def getDoctor(docName):
	docName=re.sub("\d+",'',docName)
	docName=docName.replace("^^^^^^^^^^NPI","")
	tdocName=docName.rsplit('^')
	docName=tdocName[2]+" "+tdocName[1]
	return docName

def getTestType(tt):
	if tt[0]=='M':
		return 'Molecular'
	if tt[0]=='S':
		return 'Surgical'
	if tt[0]=='F':
		if tt[1]=='H':
			return 'FISH'
		if tt[1]=='C':
			return 'FLOW'
	if tt[0]=='C':
		return 'CYTO'

		
def getDirector(tt):
	if tt=="Molecular":
		return "Weiyi Chen"
	if tt=="Surgical":
		return "Lan Wang M.D."
	if tt=="FISH":
		return "Pal Kahlon Singh"
	if tt=="CYTO":
		return "Venkata Nandula"
	if tt=="FLOW":
		return "Kelly Corcoran"
	

def getTest(test):
	return test

def computeTAT(received,reported):
	dateRec=makeDateObj(received)
	dateRep=makeDateObj(reported)
	return abs((dateRep-dateRec).days)
	

def makeDateObj(datestr):
	year=datestr[0:4]
	month=datestr[4:6]
	day=datestr[6:8]
	year=int(year)
	month=int(month)
	day=int(day)
	return datetime.date(year,month,day)

def formatDate(datestr):
	year=datestr[0:4]
	month=datestr[4:6]
	day=datestr[6:8]
	year=int(year)
	month=int(month)
	day=int(day)
	return str(month)+"/"+str(day)+"/"+str(year)
	
	
def splitDocName(dn):
	tmp=dn.split(";")
	dn=tmp[1]+tmp[0]
	return str.lstrip(dn)
	
def getPracFromDoc(doc):
	global docToPrac
	for k,v in docToPrac.items():
		if k==doc:
			return v
	return "No Practice found for "+doc

def getSalesRep(doc):
	global docToSalesRep
	for k,v in docToSalesRep.items():
		if k==doc:
			return v
	return "No Sales Rep found for "+doc
	
def searchForAddOn(case):
	global adt
	for k,v in adt.items():
		if k in case:
			return v
	return None

	


def printReportEntry(Test,TestType,TAT,Physician,SignOffDirector,dos,isAddOn):
	print "Test Type: "+TestType
	print "Test: "+Test
	print "TAT :"+str(TAT)
	print "Specimin Receive Date :"+dos
	if isAddOn==True:
		print "This is an Add On Test"
	print "Doctor :"+Physician
	print "Practice :"+getPracFromDoc(Physician)
	print "Sales Pro :"+getSalesRep(Physician)
	print "Signed Off By :"+SignOffDirector
	print	

docToPractice=""
docToSales=""
hl7file=""	
searchSalesRep=""
searchPractice=""
addOn=""
parser=argparse.ArgumentParser(description="salesEmail.py allows us to filter hl7 files into reports.  ")
parser.add_argument('-p',action="store",dest="docToPractice")
parser.add_argument('-s',action="store",dest="docToSales")
parser.add_argument('-f',action="store", dest="hl7file")
parser.add_argument('--salesrep',action="store",dest="searchSalesRep" ,default=None)
parser.add_argument('--practice',action="store",dest="searchPractice",default=None)
parser.add_argument('--addon',action="store",dest="addOn",default=None)



results=parser.parse_args()
docToPractice=results.docToPractice
docToSales=results.docToSales
hl7file=results.hl7file
searchSalesRep=results.searchSalesRep
searchPractice=results.searchPractice
addOn=results.addOn


	
# maps the doctors to practices	
rr=csv.reader(open(docToPractice,'rb'),delimiter=',',quotechar='\'')
rr.next()

docToPrac=dict()
for r in rr:
	docToPrac[splitDocName(r[0])]=r[1]
	
#maps the doctors to sales reps
rs=csv.reader(open(docToSales,'rU'),delimiter=',',quotechar='\'')
rs.next()

docToSalesRep=dict()
for r in rs:
	docToSalesRep[splitDocName(r[0])]=r[1]

#if there are Add On Cases for that day then update	
adt=dict()
if addOn != None:
	rr=csv.reader(open(addOn,'rb'),delimiter=',',quotechar='\'')
	rr.next()
	for r in rr:
		if r[1] !='':
			adt[r[0]]=redoDate(r[1])
	
	

	
reportReader=csv.reader(open(hl7file,'rU'),delimiter='|',quotechar='\'')
OrderingSite=""
TestType=""
TAT=0
Test=""
Physician=""
Practice=""
SalesRep=""
SignOffDirector=""
CaseNumber=""
isAddOn=False
speciminReceiveDate=""
for row in reportReader:
	if row[0]=='MSH' and TestType != "":
		if searchSalesRep != None and searchSalesRep==getSalesRep(Physician) and searchPractice==None:
			printReportEntry(Test,TestType,TAT,Physician,SignOffDirector,speciminReceiveDate,isAddOn)
		if searchPractice != None and searchPractice==getPracFromDoc(Physician) and searchSalesRep==None:
			printReportEntry(Test,TestType,TAT,Physician,SignOffDirector,speciminReceiveDate,isAddOn)
		if searchSalesRep==None and searchPractice==None:
			printReportEntry(Test,TestType,TAT,Physician,SignOffDirector,speciminReceiveDate,isAddOn)
	if row[0]=='PV1':
		Physician=getDoctor(row[7])
	if row[0]=='PID':
		TestType=getTestType(row[3])
		SignOffDirector=getDirector(TestType)
		CaseNumber=row[3]
		#print CaseNumber
	if row[0]=='FT1' and not row[7].isdigit() and row[7].find('-')==-1:
		Test=getTest(row[7])
		dateOfAddOn=searchForAddOn(CaseNumber)
		speciminReceiveDate=formatDate(row[4])
		if dateOfAddOn==None:
			TAT=computeTAT(row[4],row[5])
			isAddOn=False
		else:
			TAT=computeTAT(dateOfAddOn,row[5])
			isAddOn=True
		
if searchSalesRep != None and searchSalesRep==getSalesRep(Physician) and searchPractice==None:
	printReportEntry(Test,TestType,TAT,Physician,SignOffDirector,speciminReceiveDate,isAddOn)
if searchPractice != None and searchPractice==getPracFromDoc(Physician) and searchSalesRep==None:
	printReportEntry(Test,TestType,TAT,Physician,SignOffDirector,speciminReceiveDate,isAddOn)
if searchSalesRep==None and searchPractice==None:
	printReportEntry(Test,TestType,TAT,Physician,SignOffDirector,speciminReceiveDate,isAddOn)
	


	
		
		


	
	
	
	
	
	

