import os
import certifi
import uuid
import operator
import psycopg

from psycopg.rows import dict_row
from typing import TypedDict, Annotated

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage
)

from langchain_groq import ChatGroq

from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()



GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is missing. Please add it to your .env file."
    )

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=GROQ_API_KEY,
    temperature=0
)

class TravelState(TypedDict):
    messages:Annotated[list[AnyMessage],operator.add]
    user_query :str
    flight_results:str
    hotel_results:str
    itinerary:str
    llm_calls:int

############# Flight Agent  ##############
def flight_agent(state: TravelState):
    query = state['user_query']
    flight_data = search_flights(query)

    return {
        'flight_results':flight_data,
        'messages':[
            AIMessage(content='Flight resuls fetched.')
        ],
        "llm_calls":state.get('llm_calls',0) +1
    }

############# Hotel Agent  ##############

def hotel_agent(state:TravelState):
    query = f"Best hotels for {state['user_query']}"
    hotel_results = tavily_search(query)

    return {
        'hotel_results':hotel_results,
        'messages':[
            AIMessage(content='Hotel information fetched.')
        ],
        "llm_calls":state.get('llm_calls',0) +1

    }

############# Itinerary Agent  ##############

def itinerary_agent(state: TravelState):
    prompt = f"""
create a complete travel itinerary

User Query
{state['user_query']}

Flight Results:
{state['flight_results']}

Hotel Results
{state['hotel_results']}

make  the itinerary practical , budget-aware and easy to follow.
"""
    response = llm.invoke([
        SystemMessage(content='you are a expert travel planner'),
        HumanMessage(content=prompt)
    ])
    return {
        'itinerary':response.content,
        'messages':[response],
        'llm_calls':state.get('llm_calls',0) + 1
    }

############# Final Agent  ##############



def final_agent(state: TravelState):

    final_prompt = f"""
You are a professional AI travel assistant.

Create a clean, concise and useful travel plan from the information below.

USER QUERY:
{state['user_query']}

FLIGHT RESULTS:
{state['flight_results']}

HOTEL RESULTS:
{state['hotel_results']}

ITINERARY:
{state['itinerary']}

OUTPUT RULES:
- Write like ChatGPT: natural, clean and easy to read.
- Do NOT use large Markdown tables.
- Do NOT use horizontal lines like "---".
- Do NOT use excessive emojis.
- Do NOT repeat the same information.
- Do NOT invent flight prices, hotel prices, booking status or availability.
- If price is unavailable, clearly say "Price not available".
- Keep the response concise.
- Use short headings and bullet points.
- Use simple Markdown.
- Prefer bullets over tables.
- Mention important assumptions briefly.
- Do not add unnecessary travel tips unless useful.
- Do not say "Enjoy your trip" or offer additional help at the end.

Use exactly this structure:

## Trip Summary
- Destination:
- Dates:
- Travelers:
- Travel style:

## Flights
- Outbound:
- Return:
- Price: Mention "Not available" if the API does not provide it.

## Hotels
For each useful hotel:
- **Hotel name**
- Location:
- Price: If available
- Why it may fit:

## Itinerary
### Day 1
- Activity
- Activity
- Activity

### Day 2
- Activity
- Activity
- Activity

Continue only for the required number of days.

## Estimated Budget
- Flights:
- Hotels:
- Food:
- Transport:
- Activities:
- Total:

## Important Notes
- Keep only 3-5 important points.
"""

    response = llm.invoke([
        SystemMessage(
            content=(
                "You are a concise, professional travel assistant. "
                "Return clean Markdown only."
            )
        ),
        HumanMessage(content=final_prompt)
    ])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1
    }


################ build graph ################


graph = StateGraph(TravelState)


graph.add_node('flight_agent',flight_agent)
graph.add_node('hotel_agent',hotel_agent)
graph.add_node('itinerary_agent',itinerary_agent)
graph.add_node('final_agent',final_agent)


graph.add_edge(START,'flight_agent')
graph.add_edge('flight_agent',"hotel_agent")
graph.add_edge('hotel_agent','itinerary_agent')
graph.add_edge('itinerary_agent','final_agent')
graph.add_edge('final_agent',END)

## postgres checkpointer  ##
_conn = psycopg.connect(
    os.getenv("DATABASE_URL"),
    autocommit = True,
    row_factory=dict_row
)
checkpointer = PostgresSaver(_conn)
checkpointer.setup()


travel_graph = graph.compile(checkpointer=checkpointer)


# =========================
# Function for FastAPI
# =========================

def run_travel_agent(user_input: str, thread_id: str | None = None):
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = travel_graph.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ],
            "user_query": user_input,
            "flight_results": "",
            "hotel_results": "",
            "itinerary": "",
            "llm_calls": 0
        },
        config=config
    )

    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "llm_calls": result.get("llm_calls", 0),
    }