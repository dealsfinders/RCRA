def handler(event, context):
    analysis = event.get("analysisResult", {})
    severity = analysis.get("severity", "LOW")

    auto = severity in ("HIGH", "CRITICAL")

    remediation = {
        "autoRemediationEligible": auto,
        "remediationActionTaken": "NONE",
        "details": "",
    }

    if auto:
        remediation["remediationActionTaken"] = "SIMULATED_RESTART"
        remediation["details"] = (
            "MVP: simulated restart of affected service or container."
        )

    event["remediationResult"] = remediation
    return event
