# -*- coding: utf-8 -*-
"""
NOTE: SCRIPT NO LONGER FUNCTIONAL DUE TO API DEPRECIATION

"""

from ebaysdk.finding import Connection as finding
from ebaysdk.shopping import Connection as shopping
import json
from datetime import datetime
import dateutil


class DataCollector:
    
    # Opens connection to eBay's finding API and shopping API
    def __init__(self):
        self.findingapi = finding(appid="", config_file=None)
        self.shoppingapi = shopping(appid="", config_file=None)
        
    # Retrieves a list of completed Mac Mini listings
    def getCompleted(self, keywords, categoryid, condition):
        
        print('Retrieving completed listings. \n')
        
        completed = []
    
        nextpage = 1
        pages = 1
        
        numcalculated = 0
            
        while nextpage < pages+1:
            try:
                response = self.findingapi.execute('findCompletedItems', {'keywords': keywords,'categoryID':categoryid,'itemFilter':[{'name':'HideDuplicateItems','value':True,},{'name':'Condition','value':condition},{'name':'AvailableTo','value':'US'}],'paginationInput': {'pageNumber':nextpage}}).dict()
                pages = int(response['paginationOutput']['totalPages'])
                nextpage = int(response['paginationOutput']['pageNumber'])+1
                    
                for i in response['searchResult']['item']:
                    item = {'id':i['itemId'], 'title':i['title'], 'country':i['country'], 'startTime':i['listingInfo']['startTime'], 'endTime':i['listingInfo']['endTime'], 'salePrice':i['sellingStatus']['convertedCurrentPrice']['value'], 'listingType':i['listingInfo']['listingType'],'bestOfferEnabled':i['listingInfo']['bestOfferEnabled'],'sellingState':i['sellingStatus']['sellingState'], 'buyItNowAvailable':i['listingInfo']['buyItNowAvailable']}
                    
                    if(item['buyItNowAvailable'] == 'true'):
                        item['buyItNowPrice'] = i['listingInfo']['buyItNowPrice']
                        
                    if('shippingServiceCost' in i['shippingInfo'].keys()):
                        item['shippingCost'] = i['shippingInfo']['shippingServiceCost']['value']
                    else:
                        item['shippingCost'] = 'Calculated'
                        numcalculated+=1
                        
                    start = dateutil.parser.isoparse(item['startTime'])
                    end = dateutil.parser.isoparse(item['endTime'])
                    
                    duration = end-start
                    
                    duration_in_s = duration.total_seconds()
                    
                    duration_hours = divmod(duration_in_s, 360)[0]
                    
                    item['hoursToSale'] = duration_hours
                    
                    completed.append(item)
              
            except ConnectionError as e:
                    print(e)
                    pnt(e.response.dict())
            
        numitems = int(len(completed))
        
        print('{} completed listings retrieved. \n'.format(numitems))
        print('{} listings with calculated shipping. \n'.format(numcalculated))
        
        return completed
        
    # Removes duplicate listings
    def removeDups(self,completed):
        
        print('Removing duplicate listings. \n')
        numdups = 0
        
        ids = []
        nodups = []
        
        for i in completed:
            if(i['id'] not in ids):
                ids.append(i['id'])
                nodups.append(i)
            else:
                numdups = numdups + 1
                
        print('{} duplicate IDs found. \n'.format(numdups))
        print('New items list size: {} \n'.format(len(nodups)))
        return nodups

    # Retrieves shipping costs for listings with calculated shipping
    def getShippingCosts(self,completed):
        
        print('Retrieving shipping costs. \n')
        
        for item in completed:
            
            if(item['shippingCost'] == 'Calculated'):
                
                try:
                    response = self.shoppingapi.execute('GetShippingCosts',{'ItemID':item['id'],'DestinationPostalCode':'18902','DestinationCountryCode':'US'}).dict()
                    if('ShippingServiceCost' in response['ShippingCostSummary'].keys()):
                        shippingcost = response['ShippingCostSummary']['ShippingServiceCost']['value']
                        item['shippingCost'] = shippingcost
                
                except ConnectionError as e:
                    print(e)
                    print(e.response.dict())
            
                except:
                    print('Unknown error while retrieving shipping costs. Continuing to next item. \n')
                    continue
        
        return completed
            
    # Retrieves item specifics
    def getItemSpecifics(self,completed):
    
        # List for final output
        final = []
        
        # Calculates the number of API calls required (max 20 listings per call)
        iterations = int(len(completed)/20)+1 
        
        print('Retrieving item specifics. {} iterations required. \n'.format(iterations))
        
        for currentiter in range(0,iterations):
            
            # Creates a slice of listings (20 max) to be passed to the API call
            slice = completed[currentiter*20:currentiter*20+20]
            
            # A list of listing IDs in current slice
            ids = []
        
            for s in slice:
                ids.append(s['id'])
            
            try:
                response = self.shoppingapi.execute('GetMultipleItems', {'ItemID':ids, 'IncludeSelector':'ItemSpecifics'}).dict() 
                
                # A list of listing IDs in response
                responseids = []
            
                for i in response['Item']:
                    responseids.append(i['ItemID'])
            
                for item in slice:
                
                    if(item['id'] in responseids):
                    
                        loc = responseids.index(item['id'])
                    
                        itemspecifics = None
                        
                        response_items = response['Item']
                        
                    
                        if('ItemSpecifics') in response_items[loc].keys():
                        
                            if(type(response_items[loc]['ItemSpecifics']['NameValueList']) == list):
                            
                                itemspecifics = response_items[loc]['ItemSpecifics']['NameValueList']
                        
                                for i in itemspecifics:
                            
                                    item[i['Name']] = i['Value']
                                    
                        final.append(item)
                                
            except ConnectionError as e:
                print(e)
                print(e.response.dict())
                continue
                
            except:
                print('Unknown error while retrieving specifics. Continuing to next item. \n')
                
        return final
                
                    
                
                
                
            
            

        
        
        
        
        
        
        
    
        
