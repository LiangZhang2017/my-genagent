from typing import Dict, Any

def run_agent(user_id: str, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Your agent's core logic. Replace with LLM calls/tools as needed.
    Keep I/O stable: input={...} -> output={...}
    """
    question = data.get("question", "What is Newton's second law?")
    steps = [
        "Identify known quantities",
        "Recall F = m * a",
        "Solve for the unknown",
        "Check units and reasonability"
    ]
    return {
        "message": f"Hello {user_id}! Let's reason together.",
        "answer": f"Prompt: {question}",
        "next_steps": steps
    }