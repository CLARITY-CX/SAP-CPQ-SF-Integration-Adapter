from CPQ_SF_Configuration import CL_SalesforceSettings
from CPQ_SF_IntegrationSettings import CL_SalesforceQuoteParams


###############################################################################################
# Class CL_CompositeRequestReferences:
#       Class to store Salesforce API urls
###############################################################################################
class CL_SalesforceApis():

    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    DELETE = "DELETE"
    AUTH_API = "/services/oauth2/token"
    COMPOSITE_API = "/services/data/v{version}/composite".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    SOBJECT_API = "/services/data/v{version}/sobjects/{{sObject}}".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    SOBJECT_COLLECTION_API = "{sfUrl}/services/data/v{version}/composite/sobjects".format(sfUrl=str(CL_SalesforceSettings.SALESFORCE_URL), version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    GET_SOBJECT_API = "/services/data/v{version}/sobjects/{{sObject}}/{{sObjectId}}".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_SOQL_API = "/services/data/v{version}/query/".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_SOBJECT_COLLECTION_API = "/services/data/v{version}/composite/sobjects".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_DELETE_SOBJECT_COLLECTION_API = "/services/data/v{version}/composite/sobjects?ids={records}"
    CR_GET_OPPORTUNITY_API = "/services/data/v{version}/sobjects/Opportunity/{opportunityId}"
    CR_GET_ACCOUNT_API = "/services/data/v{version}/sobjects/Account/{accountId}"
    CR_GET_CONTACT_API = "/services/data/v{version}/sobjects/Contact/{{contactId}}".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_POST_CONTENT_VERSION_API = "/services/data/v{version}/sobjects/ContentVersion".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_GET_SOQL_API = "/services/data/v{version}/query/{{soql}}".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_POST_CONTENT_DOC_LINK_API = "/services/data/v{version}/sobjects/ContentDocumentLink".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_GET_OPP_PARTNERS_API = "/services/data/v{version}/sobjects/Opportunity/{{opportunityId}}/OpportunityPartnersFrom".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_GET_OPP_CONTACTS_API = "/services/data/v{version}/sobjects/Opportunity/{{opportunityId}}/OpportunityContactRoles".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    CR_GET_OPP_QUOTES_API = "/services/data/v{version}/sobjects/Opportunity/{{opportunityId}}/{quoteRel}".format(version=str(CL_SalesforceSettings.SALESFORCE_VERSION), quoteRel=str(CL_SalesforceQuoteParams.SF_OPP_QUOTE_REL))
    GET_OPPLINEITEMS_API = "{sfUrl}/services/data/v{version}/sobjects/Opportunity/{opportunityId}/OpportunityLineItems"
    GET_SOQL_API = "{sfUrl}/services/data/v{version}/query/{soql}"
    POST_CHATTER_API = "{sfUrl}/services/data/v{version}/chatter/feed-elements".format(sfUrl=str(CL_SalesforceSettings.SALESFORCE_URL), version=str(CL_SalesforceSettings.SALESFORCE_VERSION))
    GET_DESCRIBE_API = "{sfUrl}/services/data/v{version}/sobjects".format(sfUrl=str(CL_SalesforceSettings.SALESFORCE_URL), version=str(CL_SalesforceSettings.SALESFORCE_VERSION))


###############################################################################################
# Class CL_CompositeRequestReferences:
#       Class to reference Ids used in Composite Requests
###############################################################################################
class CL_CompositeRequestReferences():

    CREATE_OPP_REFID = "Create_Opportunity"
    CREATE_QUOTE_REFID = "Create_Quote"
    CREATE_SOBJECTS_REFID = "Create_SObjects"
    UPDATE_SOBJECTS_REFID = "Update_SObjects"
    GET_OPP_PARTNERS_REFID = "Get_OpportunityPartners"
    GET_OPP_CONTACTS_REFID = "Get_OpportunityContacts"
    CREATE_OPP_PARTNERS_REFID = "Create_OpportunityPartners"
    CREATE_OPP_CONTACTS_REFID = "Create_OpportunityContacts"
    DEL_OPP_PARTNERS_REFID = "Delete_OpportunityPartners"
    DEL_OPP_CONTACTS_REFID = "Delete_OpportunityContacts"
    GET_OPP_QUOTES_REFID = "Get_Opportunity_Quotes"
    GET_QUOTE_REFID = "Get_Quote"
    DEL_QUOTES_REFID = "Delete_Quotes"
    DEL_INACTIVE_QUOTES_REFID = "Delete_Inactive_Quotes"
    DEL_OPP_LINE_ITEMS_REFID = "Delete_Line_Items"
    UPDATE_PRIMARY_REFID = "Update_Primary"
    CREATE_BP_ACC = "Create_{partnerFunction}_Account"
    UPDATE_BP_ACC = "Update_{partnerFunction}_Account"
    CREATE_BP_CONTACT = "Create_{partnerFunction}_Contact"
    UPDATE_BP_CONTACT = "Update_{partnerFunction}_Contact"
    BP_CONTACT = "{partnerFunction}_Contact"
    BP_CONTACT_ID_REFID = "{partnerFunction}_Contact_ID"
    CREATE_BP_CONTACT = "Create_{partnerFunction}_Contact"
    UPDATE_BP_CONTACT = "Update_{partnerFunction}_Contact"
    ASSIGN_BP_CONTACT_REFID = "Assign_{partnerFunction}_Contact"
    INSERT_CONTENT_VERSION = "Insert_Content_Version"
    GET_CONTENT_ID = "Get_Content_Id"
    LINK_CONTENT = "Link_Content"
    GET_INTERNAL_PRODUCT_IDS_REFID = "Get_Internal_Product_Ids"
    CREATE_PRODUCTS_REFID = "Create_Products"
    UPDATE_PRODUCTS_REFID = "Update_Products"
    UPDATE_CONTACT = "Update_Contact"
    GET_OPP_ACC = "Opportunity_Account"
    GET_OPP_PARTNER_ACC = "Opportunity_Partner_Account"
    GET_OPP_ACC_PARTNER_ROLE_ACC = "Opportunity_Acc_Partner_Account"
    OPP_PARTNER_ROLE_ACC_REFID = "Get_{partnerFunction}_Opportunity_Partner_Role_Account"
    CREATE_PRICEBOOK_ENTRIES_REFID = "Create_PriceBookEntries"
    UPDATE_PRICEBOOK_ENTRIES_REFID = "Update_PriceBookEntries"
    SYNC_QUOTE_REFID = "Sync_Quote_To_Opportunity"


###############################################################################################
# Class CL_IntegrationReferences:
#       Class to keep integration references (Used in Quote Messages)
###############################################################################################
class CL_IntegrationReferences():
    
    REF_GET_QUOTES_LINKED_TO_OPPORTUNITY = "Get Quotes Linked to the Opportunity"
    REF_CREATE_OPP_LINE_ITEMS = "Create Opportunity Line Items"
    REF_GET_SF_QUOTE = "Get Salesforce Quote"
    REF_GET_OPP_LINE_ITEMS = "Opportunity Line Items"
    REF_DEL_OPP_LINE_ITEMS = "Delete Opportunity Line Items"
    REF_CREATE_ACCOUNTS = "Create Accounts"
    REF_CREATE_CONTACTS = "Create Contacts"
    REF_UPDATE_OPP_MAKE_PRIMARY = "Update Opportunity and Make Quote Primary"
    REF_OPP_PARTNERS = "Opportunity Partners"
    REF_GET_ACC_CONTACTS = "Get Accounts and Contacts"
    REF_CREATE_QUOTE_OPP = "Create Quote and Opportunity"
    REF_GET_OPP = "Get Opportunity Info"
    REF_GEN_DOC = "Send Generated Document to Salesforce"
    REF_GET_ACC = "Get Account Info"
    REF_GET_CONTACTS = "Get Contacts Info"
    REF_ASSIGN_CONTACTS = "Assign Contacts"
    REF_GET_CUSTOM_OBJECTS = "Get Custom Objects"
    REF_CR_UP_CUSTOM_OBJECTS = "Create/Update Custom Objects"
    REF_GET_OPP_ACC_PARTNER_ROLE_ACC = "Get Opportunity Account Partner Role Account"
    REF_CR_UP_PRODUCT_MASTER = "Create/Update Product Master"
    REF_CR_UP_PRICE_BOOK = "Create/Update Price Book"
    REF_GET_PRICE_BOOK = "Get Price Book Entries"
    REF_QUERY_TAG = "SOQL"
    REF_DETACH_QUOTE = "Detach Quote From Opportunity"
    REF_GET_SOBJECT_INFO = "Get SObject Info"
    REF_POST_QUOTE_NOTES = "Post Quote Notes Into Chatter"
    REF_GET_CUST_ITEM_IDS = "Get records for Quote Items to Custom Objects"
    REF_CR_UP_CUST_OBJ_ITEM = "Send Quote Items to Custom Objects"
    REF_GET_DESCRIBE = "Get Describe information on all SObjects"


###############################################################################################
# Class CL_SalesforceCustomerRoles:
#       Class to store SFDC customer default customer roles
###############################################################################################
class CL_SalesforceCustomerRoles():

    SF_BILL_TO = "Bill To"
    SF_SHIP_TO = "Ship To"
    SF_END_USER = "End User"


###############################################################################################
# Class CL_SalesforceApiLimits:
#       Class to store SFDC API limitations
###############################################################################################
class CL_SalesforceApiLimits:
    # Delete Sobject Collection API
    DELETE_API_RECORD_LIMIT = 200
    # Create Sobject Collection API
    CREATE_API_RECORD_LIMIT = 200
    # Get Internal Product Ids SOQL API (7000 line items)
    GET_INTERNAL_PRODUCT_SOQL_LIMIT = 7000
    # Get Internal Product Ids SOQL API (5000 line items)
    GET_PRICEBOOK_ENTRIES_SOQL_LIMIT = 5000
    # SOQL API Limit in a Composite Request API (5 SOQL queries per Composite Request)
    CR_SOQL_LIMIT = 5