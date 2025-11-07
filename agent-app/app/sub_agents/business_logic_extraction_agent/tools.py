import json
import logging

from google.adk.tools import ToolContext

def update_business_rule(tool_context: ToolContext, rule_id: str, new_description: str) -> bool:
    """
    Updates the description of a business rule in the catalog.
    """
    try:
        business_rules = tool_context.state.get("business_rules", [])
        if not business_rules:
            return False

        rule_found = False
        rule_counter = 1
        for file_rules in business_rules:
            try:
                rules = json.loads(file_rules["rules"])
                for i, rule in enumerate(rules):
                    current_rule_id = f"BR-{rule_counter}"
                    if current_rule_id == rule_id:
                        rules[i]["Rule Description"] = new_description
                        file_rules["rules"] = json.dumps(rules)
                        rule_found = True
                        break
                    rule_counter += 1
                if rule_found:
                    break
            except (json.JSONDecodeError, KeyError):
                continue

        if rule_found:
            tool_context.state["business_rules"] = business_rules
            logging.info("Business rule %s updated successfully.", rule_id)
            return True
        else:
            logging.warning("Business rule %s not found.", rule_id)
            return False

    except Exception as e:
        logging.error("Error updating business rule: %s", e)
        return False
