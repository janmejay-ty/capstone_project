import datetime

class RuleBasedSupervisor:
    """
    A baseline rule-based Customer Support Agent.
    Implements basic keyword matching to respond to customer inquiries.
    """
    def __init__(self) -> None:
        pass

    def handle_query(self, query: str) -> str:
        # Normalize query
        clean_query = query.strip().lower()
        
        # Log the interaction
        timestamp = datetime.datetime.now().isoformat()
        print(f"[{timestamp}] RECEIVED QUERY: '{query}'")

        if not clean_query:
            response = "Error: Query is empty."
            print(f"[{timestamp}] RESPONSE: '{response}'")
            return response

        # Keyword mapping
        if "refund" in clean_query:
            response = (
                "Standard Refund Policy: Annual plans are eligible for a full refund within 14 days of purchase. "
                "Monthly plans are non-refundable. Please contact support for manual processing."
            )
        elif "pricing" in clean_query or "plan" in clean_query:
            response = (
                "ResolveDesk AI Pricing Plans:\n"
                "- Basic: $10/user/month (Monthly billing)\n"
                "- Pro: $20/user/month (Monthly billing)\n"
                "- Enterprise: Custom pricing (Annual contract)"
            )
        elif any(kw in clean_query for kw in ["subscription", "ticket", "payment", "customer", "invoice"]):
            response = (
                "Error: Unable to retrieve live customer records or account data. "
            )
        elif "my name is" in clean_query:
            response = "Hello! Nice to meet you."
        elif "what is my name" in clean_query or "who am i" in clean_query:
            response = (
                "I do not know your name. "
            )
        else:
            response = (
                "I'm sorry, I could not understand your request. "
            )

        print(f"[{timestamp}] RESPONSE: '{response}'\n")
        return response

if __name__ == "__main__":
    # Test execution
    agent = RuleBasedSupervisor()
    agent.handle_query("What's the refund policy?")
    agent.handle_query("How do I get my money back?") # Paraphrase of refund
    agent.handle_query("Show my subscription status") # Database check
    agent.handle_query("My name is Janmejay")             # Memory check step 1
    agent.handle_query("What is my name?")            # Memory check step 2
