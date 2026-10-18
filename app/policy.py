
def assess_request(action_type, speaker_decision, deepfake_verdict): #this our security function which will be called by test/test_policy and checks its results 
    """Apply safety rules to the verification results."""
#assess_requests==>function name
#action_type==>tells what action agent needs to perform 
#speaker_decision==>tells whether speaker matched the enrolled voice 
#deepfake_verdict==>tells us whether the audio wa sclassifiedinto real or suspicious 
#action_type = "payment",speaker_decision = "no_match",deepfake_verdict = "real"
    sensitive_actions = {
        "payment",
        "account_update",
        "file_transfer",
    }
    # Never authorize sensitive actions when checks are uncertain.
    if speaker_decision != "match":
        return {
            "decision": "BLOCK",
            "reason": "The claimed speaker could not be verified.",
        }
        #decision and reason are dictonary keys ,inside our test policy if the speaker has not match then it tells to look inside the 
        #result and get the value associated with  the key decision

    if deepfake_verdict != "real":
        return {
            "decision": "BLOCK",
            "reason": "The audio is suspicious or the deepfake check is inconclusive.",
        }

    # Passing voice checks is not sufficient to authorize a payment.
    if action_type in sensitive_actions:
        return {
            "decision": "REQUIRES_CONFIRMATION",
            "reason": "Voice checks passed, but confirm independently before taking action.",
        }

    return {
        "decision": "REVIEW",
        "reason": "Voice checks passed. Review the request before proceeding.",
    }
    