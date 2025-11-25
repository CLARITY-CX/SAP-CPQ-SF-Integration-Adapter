from CPQ_SF_ContactMapping import CL_OutboundContactMapping
from CPQ_SF_IntegrationModules import CL_SalesforceIntegrationModules
from CPQ_SF_IntegrationSettings import CL_SalesforceAccountObjects, CL_SalesforceIntegrationParams, CL_GeneralIntegrationSettings, CL_SalesforceQuoteParams
from CPQ_SF_FunctionModules import get_quote_opportunity_id, set_quote_opportunity_id, get_quote_opportunity_name
from CPQ_SF_CpqHelper import EVENT_CREATE, EVENT_UPDATE
from CPQ_SF_IntegrationReferences import CL_SalesforceApiLimits as API_LIMIT, CL_CompositeRequestReferences as REF, CL_SalesforceApis as API, CL_IntegrationReferences as INT_REF
from CPQ_SF_IntegrationMessages import CL_MessageHandler, CL_IntegrationMessages
from CPQ_SF_OpportunityLineItemMapping import CL_OpportunityLineItemMapping
from CPQ_SF_PriceBookMapping import CL_PriceBookMapping
from CPQ_SF_BusinessPartnerModules import CL_BusinessPartnerModules
from CPQ_SF_ContactModules import CL_ContactIntegrationModules
from CPQ_SF_CustomObjectModules import CL_CustomObjectModules
from CPQ_SF_LineItemModules import CL_LineItemIntegrationModules
from CPQ_SF_BusinessPartnerMapping import CL_OutboundBusinessPartnerMapping
from Scripting.Quote import MessageLevel


# Function to assign partners
def assign_partners(bearerToken, opportunityId, class_sf_integration_modules, class_bp_modules, response, opportunityResponse):
	# Assign Opportunity Partners
	compositePayload = list()
	oppPartnerRolesResponse = None
	if filter(lambda x:x["SalesforceAccount"] in CL_SalesforceAccountObjects.SF_OPP_PARTNERS, CL_OutboundBusinessPartnerMapping().outboundPartnerMappings):
		if response:
			# Check if partner roles are present
			oppPartnerRolesResponse = next((resp for resp in response["compositeResponse"]
										if resp["referenceId"] == REF.GET_OPP_PARTNERS_REFID
										and resp["body"]["totalSize"] > 0), None)
		# Build composite request to assign opportunity partners
		records = class_bp_modules.build_cr_record_create_opp_partners(opportunityId, oppPartnerRolesResponse)
		if records:
			compositeRequest = class_sf_integration_modules.get_cr_sobjectcollection_payload_header(API.POST, REF.CREATE_OPP_PARTNERS_REFID, None)
			compositeRequest["body"] = {"records": records}
			compositePayload.append(compositeRequest)
	# Create Opportunity Partners - OpportunityAccountPartnerRoleAccount
	if opportunityResponse:
		if filter(lambda x:x["SalesforceAccount"] == CL_SalesforceAccountObjects.SF_OPPORTUNITY_ACC_PARTNER_ROLE_ACC, CL_OutboundBusinessPartnerMapping().outboundPartnerMappings):
			partnerPayload = class_bp_modules.build_cp_create_update_opp_acc_partner_role(bearerToken, opportunityResponse)
			if partnerPayload:
				compositePayload += partnerPayload
	if compositePayload:
		# Check Create/Update OpportunityPartner Permissions
		permissionList = [class_sf_integration_modules.build_permission_checklist(CL_SalesforceIntegrationParams.SF_OPPORTUNITY_PARTNER_OBJECT, True, True)]
		# Call REST API
		class_sf_integration_modules.post_composite_request(bearerToken, compositePayload, INT_REF.REF_OPP_PARTNERS, permissionList)


# Main execution process logic
def main():
	Quote = context.Quote
	class_sf_integration_modules = CL_SalesforceIntegrationModules(Quote, Session)
	class_msg_handler = CL_MessageHandler(Quote, Session)
	class_bp_modules = CL_BusinessPartnerModules(Quote, Session, BusinessPartnerRepository)
	class_contact_modules = CL_ContactIntegrationModules(Quote, Session)
	class_custom_object_modules = CL_CustomObjectModules(Quote, Session)
	class_line_item_modules = CL_LineItemIntegrationModules(Quote, Session)
	class_opp_line_item_modules = CL_OpportunityLineItemMapping(Quote, Session)
	#############################################
	# 1. AUTHORIZATION
	#############################################
	bearerToken = class_sf_integration_modules.get_auth2_token()
	#adminToken = class_sf_integration_modules.get_admin_auth2_token()
	#############################################
	# 2. HEADER INTEGRATION
	#############################################
	# Check if Quote is attached to an Opportunity
	opportunityId = get_quote_opportunity_id(Quote)
	# Get Salesforce Pricebook based on Markt Mapping
	sfPriceBook = class_sf_integration_modules.get_sf_pricebook_id()
	if opportunityId:
		# Stop processing if there is no Opportunity Name
		opportunityName = get_quote_opportunity_name(Quote)
		if opportunityName == "":
			class_msg_handler.add_message(CL_IntegrationMessages.NO_OPPORTUNITY_NAME, MessageLevel.Error)
			# Log Error
			Log.Error("CPQ-SFDC: Create/Update Opportunity", str(CL_IntegrationMessages.NO_OPPORTUNITY_NAME))
			# STOP PROCESSING
			return class_msg_handler
		# GET Quotes linked to the opportunity
		compositeRequest = class_sf_integration_modules.build_cr_get_opp_quotes(opportunityId)

		# All revisions from the quote will be attached to the same opportunity
		if CL_GeneralIntegrationSettings.ALL_REV_ATTACHED_TO_SAME_OPPORTUNITY:
			quoteResp = next((record for record in compositeRequest["records"]
							if record["Name"] == Quote.QuoteNumber), None)
			otherQuotes = filter(lambda resp: resp["Name"] != Quote.QuoteNumber
								, compositeRequest["records"])
		else:
			quoteResp = next((record for record in compositeRequest["records"]
							if record[CL_SalesforceQuoteParams.SF_QUOTE_ID_FIELD] == Quote.Id
							and record[CL_SalesforceQuoteParams.SF_OWNER_ID_FIELD] == Quote.OwnerId), None)
			otherQuotes = filter(lambda resp: resp[CL_SalesforceQuoteParams.SF_QUOTE_ID_FIELD] != Quote.Id
								or resp[CL_SalesforceQuoteParams.SF_OWNER_ID_FIELD] != Quote.OwnerId, compositeRequest["records"])
		# Only one quote can be linked to SF opportunity
		if CL_GeneralIntegrationSettings.ONLY_ONE_QUOTE_LINKED_TO_OPPORTUNITY:
			if otherQuotes.Count >= 1:
				class_msg_handler.add_message(CL_IntegrationMessages.ONLY_ONE_QUOTE_E_MSG, MessageLevel.Error)
				# Log Error
				Log.Error("CPQ-SFDC: Create/Update Opportunity", str(CL_IntegrationMessages.ONLY_ONE_QUOTE_E_MSG))
				# STOP PROCESSING
				return class_msg_handler

		# Create/Update Accounts
		class_bp_modules.create_update_accounts(bearerToken)

		# Create/Update Contacts
		class_contact_modules.create_update_contacts(bearerToken)

		""" ENHANCEMENTS POC -- NEW create/update/delete logic from the script """
		if not CL_GeneralIntegrationSettings.UPDATE_OPP_LINE_ITEM:
			# DELETE ALL LINE ITEMS IN SALESFORCE (Done before opportunity to allow change in Price Book)
			class_line_item_modules.delete_opp_line_items(bearerToken, opportunityId)

		""" ENHANCEMENTS POC -- NEW create/update/delete logic from the script """

		compositePayload = list()
		recordsToCreate = list()
		recordsToUpdate = list()
		# Quote object in CRM is NOT deleted every time action 'Create/Update Opportunity' is executed
		if CL_GeneralIntegrationSettings.DO_NOT_DELETE_CRM_QUOTE_ON_CREATE_UPDATE:
			if quoteResp is not None:
				# Update Salesforce Quote
				record = class_sf_integration_modules.build_cr_record_update_quote(str(quoteResp["Id"]))
				recordsToUpdate.append(record)
			else:
				# Create Salesforce Quote
				record = class_sf_integration_modules.build_cr_record_create_quote(opportunityId)
				recordsToCreate.append(record)
		else:
			# Create Salesforce Quote
			record = class_sf_integration_modules.build_cr_record_create_quote(opportunityId)
			recordsToCreate.append(record)
			if compositeRequest is not None:
				# Delete all other identical Quotes (Quote Id & Owner Id)
				quoteIdRecords = filter(lambda record:  record[CL_SalesforceQuoteParams.SF_QUOTE_ID_FIELD] == Quote.Id
										and record[CL_SalesforceQuoteParams.SF_OWNER_ID_FIELD] == Quote.OwnerId,
										compositeRequest["records"])
				if quoteIdRecords:
					quoteIdRecords = [str(record["Id"]) for record in quoteIdRecords]
					compositeRequest = class_sf_integration_modules.get_cr_sobjectcollection_payload_header(API.DELETE, REF.DEL_QUOTES_REFID, quoteIdRecords)
					compositePayload.append(compositeRequest)

		# Make Quote Primary - Set other Quotes Primary Flag to False
		if otherQuotes is not None:
			for linkedQuote in otherQuotes:
				if int(linkedQuote[CL_SalesforceQuoteParams.SF_PRIMARY_QUOTE_FIELD]):
					record = dict()
					record[CL_SalesforceQuoteParams.SF_PRIMARY_QUOTE_FIELD] = False
					record["Id"] = str(linkedQuote["Id"])
					record["attributes"] = {"type": CL_SalesforceQuoteParams.SF_QUOTE_OBJECT}
					recordsToUpdate.append(record)

		# Update Opportunity
		record = class_sf_integration_modules.build_cr_record_update_opportunity(opportunityId)
		if record:
			recordsToUpdate.append(record)
		# STOP PROCESSING
		else:
			return class_msg_handler

		# Set Opportunity Pricebook
		# NOTE: Should be set seperately from Opportunity Update to avoid the bug where the Pricebook is not set
		record = class_sf_integration_modules.build_cr_record_update_pricebook(opportunityId)
		if record:
			recordsToUpdate.append(record)

		# Build Composite Payload of Sobject Collection of records to create
		if recordsToCreate:
			compositeRequest = class_sf_integration_modules.get_cr_sobjectcollection_payload_header(API.POST, REF.CREATE_SOBJECTS_REFID, None)
			compositeRequest["body"] = {"records": recordsToCreate}
			compositePayload.append(compositeRequest)
		# Build Composite Payload of Sobject Collection of records to update
		if recordsToUpdate:
			compositeRequest = class_sf_integration_modules.get_cr_sobjectcollection_payload_header(API.PATCH, REF.UPDATE_SOBJECTS_REFID, None)
			compositeRequest["body"] = {"records": recordsToUpdate}
			compositePayload.append(compositeRequest)

		# GET Opportunity Partner Role Accounts
		compositeRequest = class_sf_integration_modules.build_cr_sobject_get_opportunity_partners(opportunityId)
		compositePayload.append(compositeRequest)

		# Get Opportunity Info
		compositeRequest = class_sf_integration_modules.build_cr_sobject_get_opportunity(opportunityId)
		compositePayload.append(compositeRequest)

		opportunityResponse = None
		if compositePayload:
			# Check Create/Update Opportunity/Quote Permissions
			permissionList = [class_sf_integration_modules.build_permission_checklist(CL_SalesforceIntegrationParams.SF_OPPORTUNITY_OBJECT, True, True),
							class_sf_integration_modules.build_permission_checklist(CL_SalesforceQuoteParams.SF_QUOTE_OBJECT, True, True, True)]
			# Call REST API
			response = class_sf_integration_modules.post_composite_request(bearerToken, compositePayload, INT_REF.REF_UPDATE_OPP_MAKE_PRIMARY, permissionList)
			opportunityResponse = next((resp for resp in response["compositeResponse"] if str(resp["referenceId"]) == CL_SalesforceIntegrationParams.SF_OPPORTUNITY_OBJECT), None)

			# Assign Opportunity Partners
			assign_partners(bearerToken, opportunityId, class_sf_integration_modules, class_bp_modules, response, opportunityResponse)

			# Assign Contacts in Salesforce according to mapping
			class_contact_modules.assign_contacts(bearerToken, opportunityId, opportunityResponse)

		# Process Custom Objects
		class_custom_object_modules.process_outbound_custom_object_mappings(bearerToken, EVENT_UPDATE)
	else:
		# Stop processing if there is no Opportunity Name
		opportunityName = get_quote_opportunity_name(Quote)
		if opportunityName == "":
			class_msg_handler.add_message(CL_IntegrationMessages.NO_OPPORTUNITY_NAME, MessageLevel.Error)
			# Log Error
			Log.Error("CPQ-SFDC: Create/Update Opportunity", str(CL_IntegrationMessages.NO_OPPORTUNITY_NAME))
			# STOP PROCESSING
			return class_msg_handler
		# Create/Update Accounts
		compositePayload = class_bp_modules.get_create_update_account_composite_payload(EVENT_CREATE)
		if compositePayload:
			# Check Create/Update Account Permissions
			permissionList = [class_sf_integration_modules.build_permission_checklist(CL_SalesforceIntegrationParams.SF_ACCOUNT_OBJECT, True, True)]
			# Call REST API
			createdAccounts = class_sf_integration_modules.post_composite_request(bearerToken, compositePayload, INT_REF.REF_CREATE_ACCOUNTS, permissionList)
			customerMappings = CL_OutboundBusinessPartnerMapping().outboundPartnerMappings
			for mapping in customerMappings:
				custResp = next((resp for resp in createdAccounts["compositeResponse"] if float(resp["httpStatusCode"]) in [200,201] and resp["referenceId"] == REF.CREATE_BP_ACC.format(partnerFunction=str(mapping["CpqPartnerFunction"])) ), None)
				if custResp:
					class_bp_modules.set_business_partner_id(mapping["CpqPartnerFunction"], str(custResp["body"]["id"]))
		# Create/Update Contacts
		compositePayload = class_contact_modules.get_create_update_contact_composite_payload(EVENT_CREATE)
		if compositePayload:
			# Check Create/Update Contact Permissions
			permissionList = [class_sf_integration_modules.build_permission_checklist(CL_SalesforceIntegrationParams.SF_CONTACT_OBJECT, True, True)]
			# Call REST API
			createdAccountsContacts = class_sf_integration_modules.post_composite_request(bearerToken, compositePayload, INT_REF.REF_CREATE_CONTACTS, permissionList)
			contactMappings = CL_OutboundContactMapping().outboundContactMappings
			for mapping in contactMappings:
				contactResp = next((resp for resp in createdAccountsContacts["compositeResponse"] if float(resp["httpStatusCode"]) in [200,201] and resp["referenceId"] == REF.CREATE_BP_CONTACT.format(partnerFunction=str(mapping["CpqPartnerFunction"]))), None)
				if contactResp:
					class_bp_modules.set_business_partner_id(mapping["CpqPartnerFunction"], str(contactResp["body"]["id"]))

		# Build Create Opportunity Composite Request
		compositePayload = list()
		record = class_sf_integration_modules.build_cr_record_create_opportunity()
		compositeRequest = class_sf_integration_modules. get_sobject_post_payload_header(CL_SalesforceIntegrationParams.SF_OPPORTUNITY_OBJECT, REF.CREATE_OPP_REFID)
		compositeRequest["body"] = record
		compositePayload.append(compositeRequest)

		# Build Create Quote Composite Request
		record = class_sf_integration_modules.build_cr_record_create_quote("@{"+REF.CREATE_OPP_REFID+".id}")
		compositeRequest = class_sf_integration_modules.get_sobject_post_payload_header(CL_SalesforceQuoteParams.SF_QUOTE_OBJECT, REF.CREATE_QUOTE_REFID)
		compositeRequest["body"] = record
		compositePayload.append(compositeRequest)

		# Check Create Opportunity/Quote Permissions
		permissionList = [  class_sf_integration_modules.build_permission_checklist(CL_SalesforceIntegrationParams.SF_OPPORTUNITY_OBJECT, True),
							class_sf_integration_modules.build_permission_checklist(CL_SalesforceQuoteParams.SF_QUOTE_OBJECT, True)]
		# Call REST API
		response = class_sf_integration_modules.post_composite_request(bearerToken, compositePayload, INT_REF.REF_CREATE_QUOTE_OPP, permissionList)

		# Get Opportunity Id and attach to Quote
		for resp in filter(lambda x: x["referenceId"] == REF.CREATE_OPP_REFID, response["compositeResponse"]):
			opportunityId = str(resp["body"]["id"])
			break
		# Attach Opportunity Id to Quote
		set_quote_opportunity_id(Quote, opportunityId)

		# Get Created Opportunity Info
		compositePayload = list()
		compositeRequest = class_sf_integration_modules.build_cr_sobject_get_opportunity(opportunityId)
		compositePayload.append(compositeRequest)
		opportunityResponse = None
		if compositePayload:
			# Call REST API
			response = class_sf_integration_modules.post_composite_request(bearerToken, compositePayload, INT_REF.REF_GET_OPP)
			opportunityResponse = next((resp for resp in response["compositeResponse"] if str(resp["referenceId"]) == CL_SalesforceIntegrationParams.SF_OPPORTUNITY_OBJECT), None)

			# Assign Opportunity Partners
			assign_partners(bearerToken, opportunityId, class_sf_integration_modules, class_bp_modules, None, opportunityResponse)

			# Assign Contacts in Salesforce according to mapping
			class_contact_modules.assign_contacts(bearerToken, opportunityId, opportunityResponse)
		# Process Custom Objects
		class_custom_object_modules.process_outbound_custom_object_mappings(bearerToken, EVENT_CREATE)
	#############################################
	# 3. LINE ITEM INTEGRATION MAPPING
	#############################################
	quoteItems = [{"item": item, "lookUps": list(), "sfId": "", "sfStandardPriceBookEntryId": "", "sfCustomPriceBookEntryId": ""} for item in Quote.GetAllItems() if (item.ProductTypeName not in CL_GeneralIntegrationSettings.PRODUCT_TYPE_EXCLUSION) and not (item.IsOptional)]
	if quoteItems:
		# Get product lookup value for each item
		for item in quoteItems:
			item["lookUps"] = class_opp_line_item_modules.get_product_lookups(Quote, item["item"])
		# Get Look Up Fields
		listOfLookUps = [item["lookUps"] for item in quoteItems if item["lookUps"]]
		if listOfLookUps:
			responses = class_line_item_modules.get_sf_internal_product_ids(bearerToken, listOfLookUps)

			# Collect Salesforce product ids
			if responses:
				for response in responses:
					quoteItems = class_line_item_modules.collect_sf_internal_product_ids(quoteItems, response)

			if CL_GeneralIntegrationSettings.CREATE_PRODUCTS_IN_SALESFORCE or CL_GeneralIntegrationSettings.UPDATE_EXISTING_PRODUCTS_IN_SALESFORCE:
				# CREATE/UPDATE PRODUCTS (PRODUCT MASTER)
				# Create/Update Products in batches of API_LIMIT.CREATE_API_RECORD_LIMIT (Currently 200)
				responses = list()
				# Remove Duplicates by lookups
				uniqueProductsToCreate = list()
				if CL_GeneralIntegrationSettings.CREATE_PRODUCTS_IN_SALESFORCE:
					# Collect line items without corresponding Salesforce products
					productsToCreate = filter(lambda x:x["sfId"]=="", quoteItems)
					for item in productsToCreate:
						if item["lookUps"] not in [i["lookUps"] for i in uniqueProductsToCreate]:
							uniqueProductsToCreate.append(item)
				# Update Products
				uniqueProductsToUpdate = list()
				if CL_GeneralIntegrationSettings.UPDATE_EXISTING_PRODUCTS_IN_SALESFORCE:
				# Collect line items for products to update
					productsToUpdate = filter(lambda x:x["sfId"]!="", quoteItems)
					# Remove duplicates by sfId
					done = set()
					for item in productsToUpdate:
						if item["sfId"] not in done:
							done.add(item["sfId"])
							uniqueProductsToUpdate.append(item)
				# Combine products to create/update
				uniqueProducts = uniqueProductsToCreate + uniqueProductsToUpdate
				for batch in range(0, len(uniqueProducts), API_LIMIT.CREATE_API_RECORD_LIMIT):
					response = class_line_item_modules.create_update_sf_product_master(bearerToken, 
																		uniqueProducts[batch:batch+API_LIMIT.CREATE_API_RECORD_LIMIT], 
																		CL_GeneralIntegrationSettings.CREATE_PRODUCTS_IN_SALESFORCE, 
																		CL_GeneralIntegrationSettings.UPDATE_EXISTING_PRODUCTS_IN_SALESFORCE)
					responses.append(response)
				# Collect sfIds of created products
				if responses:
					createdProductIds = list()
					for response in responses:
						if response["compositeResponse"]:
							createdProductsResp = next((resp for resp in response["compositeResponse"] if resp["referenceId"]==REF.CREATE_PRODUCTS_REFID), None)
							if createdProductsResp:
								createdProducts = [str(prod["id"]) for prod in createdProductsResp["body"]]
								if createdProducts:
									createdProductIds += createdProducts
					if createdProductIds:
						responses = class_line_item_modules.get_sf_product_by_ids(bearerToken, createdProductIds, listOfLookUps)
						if responses:
							for response in responses:
								quoteItems = class_line_item_modules.collect_sf_internal_product_ids(quoteItems, response)
			# Get Salesforce Standard Price Book Id
			sfStandardPriceBookId = CL_PriceBookMapping().STANDARD_PRICE_BOOK_ID
			# Call API to get existing Price Book Entries
			quoteItems = class_line_item_modules.process_collection_pricebook_ids(bearerToken, quoteItems, sfPriceBook, sfStandardPriceBookId)
			# Remove duplicates (To Create/Update Price Book Entries)
			done = set()
			quoteItemsToProcess = list()
			for item in quoteItems:
				if item["sfId"] not in done:
					done.add(item["sfId"])
					quoteItemsToProcess.append(item)
			# Create/Update Price Book Entries in batches of API_LIMIT.CREATE_API_RECORD_LIMIT (Currently 200)
			for batch in range(0, len(quoteItemsToProcess), API_LIMIT.CREATE_API_RECORD_LIMIT):
				class_line_item_modules.create_update_price_book_entries(bearerToken, quoteItemsToProcess[batch:batch+API_LIMIT.CREATE_API_RECORD_LIMIT], sfPriceBook, sfStandardPriceBookId)

			# Call API to retreive existing/created/updated Price Book Entries
			quoteItems = class_line_item_modules.process_collection_pricebook_ids(bearerToken, quoteItems, sfPriceBook, sfStandardPriceBookId)

			""" ENHANCEMENTS POC -- NEW create/update/delete logic from the script """
			# Create Line Items (Price Book Entry ID is automatically assigned in Salesforce)
			if not CL_GeneralIntegrationSettings.UPDATE_OPP_LINE_ITEM:
				class_line_item_modules.create_line_items(bearerToken, opportunityId, quoteItems, sfPriceBook)
			else:
				itemId = ",{}".format(class_opp_line_item_modules.mapping["SALESFORCE_FIELD_NAME"])
				# Get all OpportunityLineItem records to delete
				lineItems = class_line_item_modules.get_sf_opp_line_items(bearerToken, opportunityId, INT_REF.REF_GET_OPP_LINE_ITEMS, itemId)

				if lineItems:
					lineItemsToUpdate, lineItemsToDelete = class_line_item_modules.build_records(lineItems, quoteItems)

					if lineItemsToUpdate:
						class_line_item_modules.update_line_items(bearerToken, opportunityId, lineItemsToUpdate, sfPriceBook)
					if lineItemsToDelete:
						class_line_item_modules.delete_opp_line_items(bearerToken, opportunityId, lineItemsToDelete)

					class_line_item_modules.create_record(bearerToken, opportunityId, sfPriceBook, quoteItems)
			""" ENHANCEMENTS POC -- NEW create/update/delete logic from the script """

# Execute main
main()