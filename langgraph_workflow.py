from typing import TypedDict, List

from langchain_core.prompts import (
    ChatPromptTemplate
)

from langchain_core.runnables import (
    RunnableLambda
)

from langchain_groq import ChatGroq

from langgraph.graph import (
    StateGraph,
    END
)

from dotenv import load_dotenv
import os

from backend.utils.geocoder import (
    get_coordinates
)

load_dotenv()

# =================================================
# LLM
# =================================================

llm = ChatGroq(

    model="llama-3.3-70b-versatile",

    temperature=0.2,

    api_key=os.getenv("GROQ_API_KEY")
)


# =================================================
# STATE
# =================================================

class ComplaintState(TypedDict):

    complaint: str

    location: str

    workers: List[str]

    urgency: str

    department: str

    eta: str

    geo: dict

    explanation: str

    final: dict


# =================================================
# SUPERVISOR
# =================================================

supervisor_prompt = ChatPromptTemplate.from_template("""

You are a supervisor agent.

Available workers:

[
    "urgency",
    "routing",
    "geo",
    "eta"
]

Rules:

- urgency → classify severity

- routing → assign department

- geo → get coordinates

- eta → predict resolution time

Return ONLY python list.

Example:

["urgency", "routing"]

Complaint:
{complaint}

""")


def supervisor_agent(
    state: ComplaintState
):

    response = llm.invoke(

        supervisor_prompt.format_messages(

            complaint=state[
                "complaint"
            ]
        )
    )

    try:

        workers = eval(
            response.content
        )

    except:

        workers = [

            "urgency",

            "routing",

            "geo",

            "eta"
        ]

    return {
        "workers": workers
    }


# =================================================
# URGENCY AGENT
# =================================================

urgency_prompt = (
    ChatPromptTemplate
    .from_template(
        """

        Classify urgency.

        Complaint:
        {complaint}

        Return ONLY one:

        LOW
        MEDIUM
        HIGH
        CRITICAL

        """
    )
)


def urgency_worker(
    state: ComplaintState
):

    res = llm.invoke(

        urgency_prompt.format_messages(

            complaint=state[
                "complaint"
            ]
        )
    )

    return {

        "urgency":
        res.content.strip()
    }


# =================================================
# ROUTING AGENT
# =================================================

routing_prompt = (
    ChatPromptTemplate
    .from_template(
        """

        Assign department.

        Complaint:
        {complaint}

        Departments:

        - Water Department
        - Electricity Department
        - Road Maintenance
        - Sanitation Department
        - Emergency Services

        Return ONLY department.

        """
    )
)


def routing_worker(
    state: ComplaintState
):

    res = llm.invoke(

        routing_prompt.format_messages(

            complaint=state[
                "complaint"
            ]
        )
    )

    return {

        "department":
        res.content.strip()
    }


# =================================================
# GEO AGENT
# =================================================

def geo_worker(
    state: ComplaintState
):

    coords = get_coordinates(

        state["location"]
    )

    return {

        "geo": coords
    }


# =================================================
# ETA AGENT
# =================================================

eta_prompt = (
    ChatPromptTemplate
    .from_template(
        """

        Predict resolution time.

        Complaint:
        {complaint}

        Urgency:
        {urgency}

        Return SHORT answer.

        Example:
        2 hours

        """
    )
)


def eta_worker(
    state: ComplaintState
):

    res = llm.invoke(

        eta_prompt.format_messages(

            complaint=state[
                "complaint"
            ],

            urgency=state.get(
                "urgency",
                ""
            )
        )
    )

    return {

        "eta":
        res.content.strip()
    }


# =================================================
# AGGREGATOR
# =================================================

final_prompt = (
    ChatPromptTemplate
    .from_template(
        """

        Create final explanation.

        Complaint:
        {complaint}

        Urgency:
        {urgency}

        Department:
        {department}

        ETA:
        {eta}

        """
    )
)


def aggregator_agent(
    state: ComplaintState
):

    res = llm.invoke(

        final_prompt.format_messages(

            complaint=state[
                "complaint"
            ],

            urgency=state.get(
                "urgency",
                ""
            ),

            department=state.get(
                "department",
                ""
            ),

            eta=state.get(
                "eta",
                ""
            )
        )
    )

    final = {

        "complaint":

        state["complaint"],

        "location":

        state["location"],

        "urgency":

        state.get(
            "urgency"
        ),

        "department":

        state.get(
            "department"
        ),

        "estimated_resolution_time":

        state.get(
            "eta"
        ),

        "latitude":

        state[
            "geo"
        ][
            "latitude"
        ],

        "longitude":

        state[
            "geo"
        ][
            "longitude"
        ],

        "explanation":

        res.content
    }

    return {

        "final": final
    }


# =================================================
# ROUTING LOGIC
# =================================================

def route_workers(
    state: ComplaintState
):

    mapping = {

        "urgency":
        "urgency_node",

        "routing":
        "routing_node",

        "geo":
        "geo_node",

        "eta":
        "eta_node"
    }

    return [

        mapping[w]

        for w in state[
            "workers"
        ]

        if w in mapping
    ]


# =================================================
# GRAPH
# =================================================

graph = StateGraph(
    ComplaintState
)

graph.add_node(

    "supervisor",

    RunnableLambda(
        supervisor_agent
    )
)

graph.add_node(

    "urgency_node",

    RunnableLambda(
        urgency_worker
    )
)

graph.add_node(

    "routing_node",

    RunnableLambda(
        routing_worker
    )
)

graph.add_node(

    "geo_node",

    RunnableLambda(
        geo_worker
    )
)

graph.add_node(

    "eta_node",

    RunnableLambda(
        eta_worker
    )
)

graph.add_node(

    "aggregator",

    RunnableLambda(
        aggregator_agent
    )
)


# entry

graph.set_entry_point(
    "supervisor"
)


# dynamic workers

graph.add_conditional_edges(

    "supervisor",

    route_workers
)


# fan-in

graph.add_edge(
    "urgency_node",
    "aggregator"
)

graph.add_edge(
    "routing_node",
    "aggregator"
)

graph.add_edge(
    "geo_node",
    "aggregator"
)

graph.add_edge(
    "eta_node",
    "aggregator"
)

graph.add_edge(
    "aggregator",
    END
)


app = graph.compile()


# =================================================
# TEST
# =================================================

if __name__ == "__main__":

    result = app.invoke({

        "complaint":

        "Transformer explosion near Tikonia",

        "location":

        "Tikonia Haldwani"
    })

    print(result["final"])