from CPQ_SF_FunctionModules import is_action_allowed
from CPQ_SF_IntegrationSettings import CL_GeneralIntegrationSettings

# Constants
CREATE = "create"
EDIT = "edit"
NEW = "new"
VIEW = "view"
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

# Main
externalParameters = context.ExternalParameters
action = get_param(externalParameters, "action")

# Clear Session for Landing from CRM
opportunityId = get_param(externalParameters, "opportunityId", "").strip()
Session[opportunityId] = None
Session["Query"] = None
test = get_param(externalParameters, "new", "nothing")
Trace.Write("test value: " + str(test))

# Set SF User Session Token & Opportunity Id
Session["apiSessionID"] = get_param(externalParameters, "apiSessionID")
Session["OpportunityId"] = opportunityId

# Execute action
if action == CREATE:
    redirectionUrl = create_quote(externalParameters)
elif action == EDIT:
    redirectionUrl = edit_quote(externalParameters)
elif action == NEW:
    redirectionUrl = ScriptExecutor.Execute("CPQ_SF_LandingOnCatalogue")
elif action == VIEW:
    redirectionUrl = ScriptExecutor.Execute(
        "CPQ_SF_ViewQuote",
        {"externalParameters": externalParameters}
    )
