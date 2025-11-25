from CPQ_SF_FunctionModules import is_action_allowed
from CPQ_SF_IntegrationSettings import CL_GeneralIntegrationSettings

# Constants
CREATE = "create"
EDIT = "edit"
NEW = "new"
VIEW = "view"
# action Edit -> Id = 13
EDIT_ACTION_ID = 13

# Helpers
def get_param(params, key, default=None):
    """Safe dictionary access."""
    return params[key] if key in params else default

def create_quote(externalParams):
    uniqueId = get_param(externalParams, "uniqueId")
    if uniqueId:
        if not Session[uniqueId]:
            Session[uniqueId] = ScriptExecutor.Execute(
                "CPQ_SF_CreateQuote",
                {"externalParameters": externalParams, "createQuote": True}
            )
        return Session[uniqueId]
    return ScriptExecutor.Execute(
        "CPQ_SF_CreateQuote",
        {"externalParameters": externalParams, "createQuote": True}
    )

def edit_quote(externalParams):
    """Edit or view the quote based on permissions."""
    if CL_GeneralIntegrationSettings.ALL_REV_ATTACHED_TO_SAME_OPPORTUNITY:
        quote_number = get_param(externalParams, "quotenumber")
        quote = QuoteHelper.Get(quote_number)
    else:
        quote_id = get_param(externalParams, "quoteId")
        quote = QuoteHelper.Get(float(quote_id))

    if is_action_allowed(quote, User, externalParams, EDIT_ACTION_ID):
        return ScriptExecutor.Execute(
            "CPQ_SF_EditQuote",
            {"externalParameters": externalParams, "quote": quote}
        )
    return ScriptExecutor.Execute(
        "CPQ_SF_ViewQuote",
        {"externalParameters": externalParams}
    )

# Get parameters
externalParameters = context.ExternalParameters
# Create Quote or Edit Quote
action = externalParameters["action"]
# Clear Session OnLandingFromCRM
opportunityId = externalParameters["opportunityid"].strip()

# Clear Session OnLandingFromCRM
Session[opportunityId] = None
Session["Query"] = None

# Set SF User Session Token
Session["apiSessionID"] = externalParameters["apiSessionID"]
# Set Opportunity Id in Session
Session["OpportunityId"] = opportunityId

# Dispose Quote from Session (If Quote was opened previously)
if Quote is not None:
    Quote.Dispose()

# Refresh Market Visibility
User.RefreshMarkets()

if action == CREATE:
    redirectionUrl = create_quote(externalParameters)
elif action == EDIT:
    redirectionUrl = edit_quote(externalParameters)
elif action == NEW:
    redirectionUrl = ScriptExecutor.Execute("CPQ_SF_LandingOnCatalogue")
elif action == VIEW:
    redirectionUrl = ScriptExecutor.Execute("CPQ_SF_ViewQuote", {"externalParameters": externalParameters})