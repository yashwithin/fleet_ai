from langchain.tools import tool
from rich import print
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv

from sqlite_db import (
    create_ride,
    file_grievance,
    get_customer,
    get_driver,
    get_ride_eta,
)

load_dotenv()

# ----------------------------
# LLMs
# ----------------------------
anthropic = ChatAnthropic(model="claude-3-haiku-latest", max_tokens=1000)

# ----------------------------
# TOOLS
# ----------------------------


@tool
def book_ride_tool(customer_id: str, pickup: str, dropoff: str) -> dict:
    """Book a ride for a customer given pickup and dropoff locations."""
    customer_id = customer_id.strip().upper()

    ride_id, ride_info = create_ride(customer_id, pickup, dropoff)

    if not ride_id:
        return {"status": "error", "message": ride_info}

    driver = get_driver(ride_info["driver_id"]) or {}

    return {
        "status": "success",
        "customer_id": customer_id,
        "ride_id": ride_id,
        "pickup": ride_info["pickup"],
        "dropoff": ride_info["dropoff"],
        "fare": ride_info["fare"],
        "eta": ride_info["eta_minutes"],
        "distance": ride_info["distance_km"],
        "driver": {
            "name": driver.get("name"),
            "vehicle": driver.get("vehicle"),
            "plate": driver.get("plate"),
            "rating": driver.get("rating"),
        },
    }


@tool
def handle_grievance_tool(
    customer_id: str, ride_id: str, category: str, description: str
) -> dict:
    """File a grievance."""
    customer_id = customer_id.strip().upper()
    customer = get_customer(customer_id)
    if not customer:
        return {"status": "error", "message": "Customer not found"}

    file_grievance(customer_id, ride_id, category, description)

    return {
        "status": "success",
        "message": "Your complaint has been registered successfully.",
    }


@tool
def check_eta_tool(ride_id: str) -> dict:
    """Get ETA details for a ride."""

    data, err = get_ride_eta(ride_id)

    if err:
        return {"status": "error", "message": err}

    return {
        "status": "success",
        "ride_id": data["ride_id"],
        "eta": data["eta_minutes"],
        "delay": data["delay_minutes"],
        "ride_status": data["status"],
    }


@tool
def wallet_balance_tool(customer_id: str) -> dict:
    """Get wallet balance."""

    customer = get_customer(customer_id)

    if not customer:
        return {"status": "error", "message": "Customer not found"}

    return {
        "status": "success",
        "customer_id": customer_id,
        "name": customer["name"],
        "wallet_balance": customer["wallet"],
    }


# ----------------------------
# TOOL REGISTRY
# ----------------------------
tools = {
    tool.name: tool
    for tool in [
        book_ride_tool,
        handle_grievance_tool,
        check_eta_tool,
        wallet_balance_tool,
    ]
}

llm_with_tools = anthropic.bind_tools(list(tools.values()))

# # ----------------------------
# # FORMATTER PROMPT
# # ----------------------------
# final_prompt = ChatPromptTemplate.from_messages(
#     [
#         (
#             "system",
#             """
# You are a  ride assistant.
# Convert tool output into a clean, user-friendly message.

# Rules:
# - Be short and conversational
# - Include important info: driver name, car, fare, ETA, wallet balance
# - Do NOT show JSON or technical details
# - Do NOT explain system logic
# - Personalize using user's name if available
# """,
#         ),
#         ("human", "{topic}"),
#     ]
# )


# ----------------------------
# MAIN AGENT FUNCTION (IMPORTANT)
# ----------------------------
def run_agent(user_input):
    messages = [HumanMessage(content=user_input)]

    result = llm_with_tools.invoke(messages)
    print(result)
    if result.tool_calls:
        tool_call = result.tool_calls[0]

        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        tool_output = tools[tool_name].invoke(tool_args)

        return {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "tool_output": tool_output,
        }

    return {"type": "chat", "message": result.content}
