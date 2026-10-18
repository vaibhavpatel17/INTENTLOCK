

@app.post("/api/request-number-change")
def request_number_change(request: StartNumberChangeRequest):
    if not request.new_number.isdigit() or len(request.new_number) != 10:
        raise HTTPException(status_code=400, detail="Enter a valid 10-digit phone number.")

    analysis = get_valid_analysis(request.analysis_request_id)
    if analysis["action_type"] != "account_update":
        raise HTTPException(status_code=403, detail="Analysis was not for an account update.")
    if analysis["policy_decision"] != "REQUIRES_CONFIRMATION":
        raise HTTPException(
            status_code=403,
            detail=f"INTENTLOCK policy does not permit this action. Decision: {analysis['policy_decision']}",
        )

    request_id = str(uuid.uuid4())
    confirmation_code = f"{secrets.randbelow(1_000_000):06d}"
    pending_changes[request_id] = {
        "new_number": request.new_number,
        "analysis_request_id": request.analysis_request_id,
        "policy_decision": analysis["policy_decision"],
        "confirmation_code": confirmation_code,
        "confirmed": False,
        "explicitly_authorized": False,
        "expires_at": time.time() + REQUEST_TTL_SECONDS,
    }
    # Demo convenience only. Never expose confirmation codes in production logs.
    print(f"Demo confirmation code for {request_id}: {confirmation_code}")
    return {
        "request_id": request_id,
        "message": "Demo request created. Check the backend terminal.",
        "expires_in_seconds": REQUEST_TTL_SECONDS,
    }


@app.post("/api/confirm-number-change")
def confirm_number_change(request: ConfirmNumberChangeRequest):
    pending = get_valid_pending_request(request.request_id)
    analysis = get_valid_analysis(pending["analysis_request_id"])
    if (
        analysis["action_type"] != "account_update"
        or analysis["policy_decision"] != "REQUIRES_CONFIRMATION"
        or pending["policy_decision"] != analysis["policy_decision"]
    ):
        raise HTTPException(status_code=403, detail="INTENTLOCK policy denied this action.")

    if not secrets.compare_digest(request.confirmation_code, pending["confirmation_code"]):
        raise HTTPException(status_code=403, detail="Incorrect confirmation code. Check the latest code.")

    pending["confirmed"] = True
    return {
        "status": "CONFIRMED",
        "message": "Demo confirmation recorded.",
        "request_id": request.request_id,
        "message_for_next_step": "A separate policy authorization is still required before execution.",
    }


@app.post("/api/authorize-number-change")
def authorize_number_change(request: AuthorizeNumberChangeRequest):
    # Set INTENTLOCK_ADMIN_TOKEN in the backend .env. Never put it in frontend code.
    expected_token = os.getenv("INTENTLOCK_ADMIN_TOKEN")
    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Explicit authorization is not configured. Set INTENTLOCK_ADMIN_TOKEN in the backend environment.",
        )
    if not secrets.compare_digest(request.admin_token, expected_token):
        raise HTTPException(status_code=403, detail="Explicit policy authorization was denied.")

    pending = get_valid_pending_request(request.request_id)
    analysis = get_valid_analysis(pending["analysis_request_id"])
    if not pending["confirmed"]:
        raise HTTPException(status_code=403, detail="Independent confirmation is required before approval.")
    if (
        analysis["action_type"] != "account_update"
        or analysis["policy_decision"] != "REQUIRES_CONFIRMATION"
        or pending["policy_decision"] != "REQUIRES_CONFIRMATION"
    ):
        raise HTTPException(status_code=403, detail="The current policy state is not eligible for approval.")

    # A separate trusted reviewer explicitly authorizes this simulated action.
    analysis["policy_decision"] = "ALLOW"
    pending["policy_decision"] = "ALLOW"
    pending["explicitly_authorized"] = True
    return {
        "status": "AUTHORIZED",
        "message": "A separate trusted reviewer explicitly authorized this demo action.",
        "request_id": request.request_id,
    }


@app.post("/api/change-number")
def change_number(request: ExecuteNumberChangeRequest):
    pending = get_valid_pending_request(request.request_id)
    analysis = get_valid_analysis(pending["analysis_request_id"])
    if not pending["confirmed"]:
        raise HTTPException(status_code=403, detail="Independent confirmation is required.")

    # Fail closed: both server-side policy records must explicitly say ALLOW.
    if (
        analysis["action_type"] != "account_update"
        or analysis["policy_decision"] != "ALLOW"
        or pending["policy_decision"] != "ALLOW"
        or not pending["explicitly_authorized"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Execution denied: explicit policy authorization is required. Confirmation alone is not authorization.",
        )

    result = change_registered_number(pending["new_number"], authorized=True)
    if result["status"] != "SUCCESS":
        raise HTTPException(status_code=400, detail=result["message"])

    del pending_changes[request.request_id]
    analysis_results.pop(pending["analysis_request_id"], None)
    return result
