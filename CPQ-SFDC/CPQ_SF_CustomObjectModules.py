from CPQ_SF_IntegrationModules import CL_SalesforceIntegrationModules
from CPQ_SF_IntegrationReferences import CL_SalesforceApis as API, CL_IntegrationReferences as INT_REF, CL_SalesforceApiLimits as API_LIMIT
from CPQ_SF_CpqHelper import EVENT_CREATE, EVENT_UPDATE
from CPQ_SF_CustomObjectMapping import CL_CustomObjectMapping


###############################################################################################
# Class CL_CustomObjectModules:
#       Class to store integration functions related to custom objects
###############################################################################################
class CL_CustomObjectModules(CL_SalesforceIntegrationModules):

    ###############################################################################################
    # Function process inbound custom object mappings (Salesforce -> CPQ)
    ###############################################################################################
    def process_inbound_custom_object_mappings(self, bearerToken, event):
        class_custom_object_mapping = CL_CustomObjectMapping(self.Quote, self.TagParserQuote, None, None)
        mappings = filter(lambda x: x["Inbound"], class_custom_object_mapping.custom_object_mappings())
        if mappings:
            queryObjResponses, linkedToQuoteResponses = self.get_custom_objects(bearerToken, mappings)
            if queryObjResponses or linkedToQuoteResponses:
                # Process responses for Query and Linked to Quote custom objects
                for objectType in [{"Linked_To_Quote" : False, "Responses": queryObjResponses}, {"Linked_To_Quote" : True, "Responses": linkedToQuoteResponses}]:
                    for mapping in filter(lambda x:x["Linked_To_Quote"] is objectType["Linked_To_Quote"], mappings):
                        customObject = None
                        if objectType["Responses"]:
                            for response in objectType["Responses"]:
                                # Get Custom Object Response
                                customObject = next((resp["body"] for resp in response["compositeResponse"] if resp["referenceId"] == mapping["Name"]), None)
                                if customObject:
                                    break
                            # Process Mappings
                            if customObject:
                                if event == EVENT_CREATE:
                                    class_custom_object_mapping.on_quote_create_custom_object_mapping(self.Quote, self.TagParserQuote, customObject, mapping["Name"])
                                elif event == EVENT_UPDATE:
                                    class_custom_object_mapping.on_quote_update_custom_object_mapping(self.Quote, self.TagParserQuote, customObject, mapping["Name"])
                                class_custom_object_mapping.on_quote_createupdate_custom_object_mapping(self.Quote, self.TagParserQuote, customObject, mapping["Name"])


    ###############################################################################################
    # Function to get custom obect ids for Query types
    ###############################################################################################
    def get_query_custom_object_ids(self, bearerToken, mappings):
        response = None
        compositePayload = list()
        for mapping in filter(lambda x: x["Linked_To_Quote"] is False, mappings):
            compositeRequest = self.build_soql_query_composite_payload(mapping["Query"], mapping["Name"])
            compositePayload.append(compositeRequest)
        if compositePayload:
            # Call REST API
            response = self.post_composite_request(bearerToken, compositePayload, INT_REF.REF_GET_CUSTOM_OBJECTS)
        return response

    ###############################################################################################
    # Function to get custom obect information
    ###############################################################################################
    def get_custom_objects(self, bearerToken, mappings):
        queryObjResponses = list()
        queryObjResponse = None
        linkedToQuoteResponses = list()
        linkedToQuoteResponse = None
        # For Custom Object Queries
        custObjQueryMappings = filter(lambda x: x["Linked_To_Quote"] is False, mappings)
        responses = list()
        # Execute queries in batches of 5 as per Composite Request limitation in API_LIMIT.CR_SOQL_LIMIT
        for batch in range(0, len(custObjQueryMappings), API_LIMIT.CR_SOQL_LIMIT):
            response = self.get_query_custom_object_ids(bearerToken, custObjQueryMappings[batch:batch+API_LIMIT.CR_SOQL_LIMIT])
            if response: 
                responses.append(response)
        if responses:
            for response in responses:
                if response["compositeResponse"]:
                    compositePayload = list()
                    compositeRequest = dict()
                    for mapping in mappings:
                        # Get Custom Object response
                        customObjectResponse = next((resp for resp in response["compositeResponse"] if resp["referenceId"] == mapping["Name"] and resp["body"]["totalSize"] > 0), None)
                        if customObjectResponse:
                            # Get Custom Object Id
                            customObjectRecord = next((rec for rec in customObjectResponse["body"]["records"]), None)
                            if customObjectRecord:
                                customObjectId = str()
                                for attr in customObjectRecord:
                                    if attr.Name != "attributes":
                                        customObjectId = str(getattr(customObjectRecord, attr.Name))
                                        break
                                # Get Custom Object details
                                if customObjectId != "":
                                    url = API.GET_SOBJECT_API.format(sObject=str(mapping["Type"]), sObjectId=str(customObjectId))
                                    method = API.GET
                                    compositeRequest = self.build_cr_sobject_request(url, method, None, mapping["Name"])
                                    compositePayload.append(compositeRequest)

                    if compositePayload:
                        # Call REST API
                        queryObjResponse = self.post_composite_request(bearerToken, compositePayload, INT_REF.REF_GET_CUSTOM_OBJECTS)
                        if queryObjResponse:
                            queryObjResponses.append(queryObjResponse)
        # For Custom Object Linked to Quote
        compositePayload = list()
        try:
            customObjectQuoteTable = self.Quote.QuoteTables["CPQ_SF_QUOTE_CUSTOM_OBJECTS"]
        except SystemError as e:
            Log.Error("CPQ-SFDC: Custom Object table not found", str(e))
            customObjectQuoteTable = None
        if customObjectQuoteTable:
            for mapping in filter(lambda x: x["Linked_To_Quote"], mappings):
                customObject = next((row for row in customObjectQuoteTable.Rows if row.GetColumnValue("CUSTOM_OBJECT_NAME") == mapping["Name"]), None)
                if customObject:
                    customObjectId = customObject.GetColumnValue("CUSTOM_OBJECT_ID")
                    # Get Custom Object details
                    if customObjectId != "":
                        url = API.GET_SOBJECT_API.format(sObject=str(mapping["Type"]), sObjectId=str(customObjectId))
                        method = API.GET
                        compositeRequest = self.build_cr_sobject_request(url, method, None, mapping["Name"])
                        compositePayload.append(compositeRequest)
        if compositePayload:
            # Call REST API
            linkedToQuoteResponse = self.post_composite_request(bearerToken, compositePayload, INT_REF.REF_GET_CUSTOM_OBJECTS)
            if linkedToQuoteResponse:
                linkedToQuoteResponses.append(linkedToQuoteResponse)
        return queryObjResponses, linkedToQuoteResponses

    ###############################################################################################
    # Function process outbound custom object mappings (CPQ -> Salesforce)
    ###############################################################################################
    def process_outbound_custom_object_mappings(self, bearerToken, event):
        class_custom_object_mapping = CL_CustomObjectMapping(self.Quote, self.TagParserQuote, None, None)
        mappings = filter(lambda x: x["Outbound"], class_custom_object_mapping.custom_object_mappings())
        if mappings:
            linkedToQuoteMappings = filter(lambda x: x["Linked_To_Quote"], mappings)
            if linkedToQuoteMappings:
                self.create_update_linked_to_quote_obj(bearerToken, linkedToQuoteMappings, event)
            queryMappings = filter(lambda x: x["Query"] != "" and x["Linked_To_Quote"] is False, mappings)
            if queryMappings:
                self.create_update_query_custom_obj(bearerToken, queryMappings, event)

    ###############################################################################################
    # Function to create/update custom object (CPQ -> Salesforce)
    ###############################################################################################
    def create_update_query_custom_obj(self, bearerToken, mappings, event):
        response = None
        # Get Custom Object Ids
        responses = list()
        # Execute queries in batches of 5 as per Composite Request limitation in API_LIMIT.CR_SOQL_LIMIT
        for batch in range(0, len(mappings), API_LIMIT.CR_SOQL_LIMIT):
            response = self.get_query_custom_object_ids(bearerToken, mappings[batch:batch+API_LIMIT.CR_SOQL_LIMIT])
            if response: 
                responses.append(response)
        if responses:
            for response in responses:
                if response["compositeResponse"]:
                    compositePayload = list()
                    permissionList = list()
                    for mapping in mappings:
                        # Get Custom Object response
                        customObjectResponse = next((resp for resp in response["compositeResponse"] if resp["referenceId"] == mapping["Name"] and resp["body"]["totalSize"] > 0), None)
                        customObjectId = str()
                        if customObjectResponse:
                            # Get Custom Object Id
                            customObjectRecord = next((rec for rec in customObjectResponse["body"]["records"]), None)
                            if customObjectRecord:
                                for attr in customObjectRecord:
                                    if attr.Name != "attributes":
                                        customObjectId = str(getattr(customObjectRecord, attr.Name))
                                        break
                        # Build Create/Update Custom Object Composite Request
                        compositeRequest = self.build_cr_create_update_custom_object(mapping, customObjectId, event, mapping["Create"])
                        if compositeRequest:
                            compositePayload.append(compositeRequest)
                            # Build Permission List
                            permission = self.build_permission_checklist(mapping["Type"], True, True, True)
                            if permission: permissionList.append(permission)
                    if compositePayload:
                        # Call REST API
                        self.post_composite_request(bearerToken, compositePayload, INT_REF.REF_CR_UP_CUSTOM_OBJECTS, permissionList)


    ###############################################################################################
    # Function to create/update custom object Linked to Quote (CPQ -> Salesforce)
    ###############################################################################################
    def create_update_linked_to_quote_obj(self, bearerToken, mappings, event):
        response = None
        # Get Custom Object Id
        try:
            customObjectQuoteTable = self.Quote.QuoteTables["CPQ_SF_QUOTE_CUSTOM_OBJECTS"]
        except SystemError as e:
            Log.Error("CPQ-SFDC: Custom Object table not found", str(e))
            customObjectQuoteTable = None
        if customObjectQuoteTable:
            compositePayload = list()
            permissionList = list()
            for mapping in mappings:
                customObject = next((row for row in customObjectQuoteTable.Rows if row.GetColumnValue("CUSTOM_OBJECT_NAME") == mapping["Name"]), None)
                customObjectId = None
                if customObject:
                    customObjectId = customObject.GetColumnValue("CUSTOM_OBJECT_ID")
                compositeRequest = self.build_cr_create_update_custom_object(mapping, customObjectId, event, mapping["Create"])
                if compositeRequest:
                    # Build Permission List
                    permission = self.build_permission_checklist(mapping["Type"], True, True, True)
                    if permission: permissionList.append(permission)
                    compositePayload.append(compositeRequest)
            if compositePayload:
                # Call REST API
                response = self.post_composite_request(bearerToken, compositePayload, INT_REF.REF_CR_UP_CUSTOM_OBJECTS, permissionList)
                # Add/Update to Quote Table
                if response:
                    self.update_custom_object_quote_table(customObjectQuoteTable, mappings, response)
        return response

    ###############################################################################################
    # Function to update custom object Quote Table based on response
    ###############################################################################################
    def update_custom_object_quote_table(self, customObjectQuoteTable, mappings, response):
        for mapping in mappings:
            customObjectResp = next((resp for resp in response["compositeResponse"]
                                     if resp["referenceId"] == mapping["Name"]
                                     and resp["httpStatusCode"] == 201), None)
            if customObjectResp:
                # Get Custom Object Id
                customObjectId = str(customObjectResp["body"]["id"])
                if customObjectId != "":
                    customObject = next((row for row in customObjectQuoteTable.Rows if row.GetColumnValue("CUSTOM_OBJECT_NAME") == mapping["Name"]), None)
                    # Update row
                    if customObject:
                        customObject.SetColumnValue("CUSTOM_OBJECT_ID", customObjectId)
                    # Add row
                    else:
                        newRow = customObjectQuoteTable.AddNewRow()
                        newRow.SetColumnValue("CUSTOM_OBJECT_NAME", mapping["Name"])
                        newRow.SetColumnValue("CUSTOM_OBJECT_ID", customObjectId)
        # Save Quote Table
        customObjectQuoteTable.Save()

    ###############################################################################################
    # Function to get composite request to create/update Custom Object
    ###############################################################################################
    def build_cr_create_update_custom_object(self, mapping, customObjectId, event, createFlag):
        compositeRequest = None
        customObjectRecord = dict()
        class_custom_object_mapping = CL_CustomObjectMapping(self.Quote, self.TagParserQuote, None, None)
        if event == EVENT_CREATE:
            customObjectRecord = class_custom_object_mapping.on_opp_create_custom_object_mapping(self.Quote, self.TagParserQuote, mapping["Name"])
        elif event == EVENT_UPDATE:
            customObjectRecord = class_custom_object_mapping.on_opp_update_custom_object_mapping(self.Quote, self.TagParserQuote, mapping["Name"])
        customObjectRecord.update(class_custom_object_mapping.on_opp_createupdate_custom_object_mapping(self.Quote, self.TagParserQuote, mapping["Name"]))

        if customObjectRecord:
            url = str()
            method = str()
            if customObjectId:
                # Update
                url = API.GET_SOBJECT_API.format(sObject=str(mapping["Type"]), sObjectId=str(customObjectId))
                method = API.PATCH
            else:
                # Create
                if createFlag:
                    url = API.SOBJECT_API.format(sObject=str(mapping["Type"]))
                    method = API.POST
            if url and method:
                compositeRequest = self.build_cr_sobject_request(url, method, None, mapping["Name"])
                compositeRequest["body"] = customObjectRecord

        return compositeRequest
