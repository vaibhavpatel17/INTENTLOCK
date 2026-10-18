# Store a fake account for our INTENTLOCK demo.
# This does not change any real account.
demo_account = {
    "phone": "9000000000"
}


def change_registered_number(new_number, authorized):
    # Block the action if authorization has not been granted.
    if not authorized:
        return {
            "status": "BLOCKED",
            "message": "INTENTLOCK denied this action."
        }

    # Basic validation for our demo phone number.
    if not new_number.isdigit() or len(new_number) != 10:
        return {
            "status": "ERROR",
            "message": "Enter a valid 10-digit phone number."
        }

    # Update the fake account only after the checks pass.
    demo_account["phone"] = new_number

    return {
        "status": "SUCCESS",
        "message": "Demo phone number updated successfully.",
        "phone": demo_account["phone"]
    }