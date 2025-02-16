import uuid
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

from openai import OpenAI
from external_functions import query_perplexity, send_email, video_analysis
from utils import *
import schemas

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
perplexity_client = OpenAI(api_key=os.getenv("PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai")


def init_agent(nodes: list[schemas.NodeV2], active_node: str):
    brief = load_brief("demo/brief.txt")
    init_brief_prompt = """
    You are helping create a root node for a research project. Given a project brief:
    1. Generate a 5-word title that captures the key focus
    2. Write a concise summary (max 200 words) that captures the essence of the investigation
    Format the response as JSON with "title" and "content" fields.
    """
    
    messages = [
        {"role": "system", "content": init_brief_prompt},
        {"role": "user", "content": f"Project brief:\n{brief}"}
    ]
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        response_format={"type": "json_object"}
    )
    
    response_content = response.choices[0].message.content
    parsed_response = schemas.ModelOutput.model_validate(json.loads(response_content))
    
    root_node_id = create_node(nodes, parsed_response.title, "root", parsed_response.content, "brief", datetime.now())
    print(f"Root node created with id: {root_node_id}")
    # print content
    try:
        root_node = get_node_by_id(nodes, root_node_id)
    except Exception as e:
        print(f"Error getting node by id: {e}")
        root_node = None
    print(f"node_content: {root_node.content}")
    execute_mode_ii(nodes, root_node_id)
    breakpoint()

def execute_mode_ii(nodes: list[schemas.NodeV2], active_node: str):
    """
    Executes mode II of the research agent, which expands knowledge by analyzing 
    the situation and generating new insights for the active node.
    """
    if not active_node:
        print("No active node selected")
        return

    current_node = get_node_by_id(nodes, active_node)
    if not current_node:
        print(f"Could not find active node with id: {active_node}")
        return

    current_node_name = current_node.name
    current_node_content = current_node.content

    messages = [
        {"role": "system", "content": mode_ii},
        {"role": "user", "content": f"""

         The current research node:
         Title: {current_node_name}
         Content: {current_node_content}

         Generate relevant insights and create new nodes.
"""}
    ]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=mode_ii_tools,
        temperature=0.7
    )

    message = response.choices[0].message
    
    if hasattr(message, "tool_calls") and message.tool_calls:
        messages.append(message)
        for tool_call in message.tool_calls:
            if tool_call.function.name == "create_node":
                args = json.loads(tool_call.function.arguments)
                breakpoint()
                child_id = create_node(
                    nodes=nodes,
                    name=args["name"],
                    type=args["type"],
                    content=args["content"],
                    source="mode_ii",
                    timestamp=datetime.now()
                )
                update_node_children(nodes, active_node, child_id)
                print(f"Created new node: {args['name']}")
    
    print_nodes(nodes)
    return


def process_chat(user_message: str, chat_history: list) -> dict:
    """
    Process the chat message using the OpenAI API with function calling.
    The chat_history is a list of dicts with keys "role" and "message".
    This function returns a dict with the assistant's final message,
    along with any new nodes/edges generated.

    Enhanced functionality:
     - A system message instructs expansions (creating multiple nodes, edges).
     - We've added create_edge to link nodes in the graph.
    """

    # System message ensures the model is aware it can create multiple nodes
    # and optionally connect them with edges if the user requests expansions.
    system_instructions = {
        "role": "system",
        "content": (
            "You are an autonomous research agent. You have the following abilities:\n"
            "1) If the user says 'tell me more about [topic]', propose multiple subtopics as new nodes.\n"
            "2) Use create_node repeatedly to add the subtopics.\n"
            "3) Link them to their parent with create_edge.\n"
            "4) Summarize the expansions in your final assistant message.\n\n"
            "Key details:\n"
            "- You have access to the following functions:\n"
            "  [send_email, query_perplexity, video_analysis, create_node, create_edge]\n"
            "- Provide expansions as multiple node creations if relevant.\n"
            "- If you want to gather proprietary feedback from the user, place it in the final chat message.\n"
            "Respond to the user after you finish all expansions or function calls.\n"
        ),
    }

    messages = [system_instructions]
    messages.extend(
        {"role": msg["role"], "content": msg["message"]} for msg in chat_history
    )
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, tools=tools, temperature=0.7
    )
    message = response.choices[0].message

    assistant_message = ""
    new_nodes = []
    new_edges = []

    if hasattr(message, "tool_calls") and message.tool_calls:
        messages.append(message)
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments_str = tool_call.function.arguments

            try:
                args = json.loads(arguments_str)
            except Exception as e:
                logging.error(f"Error parsing function arguments: {e}")
                args = {}

            if function_name == "send_email":
                result = send_email(**args)
                node = {
                    "id": str(uuid.uuid4()),
                    "node_class": "email",
                    "content": {
                        "text": (
                            f"Email sent to: {args.get('to')}\n"
                            f"Subject: {args.get('subject')}\n"
                            f"Body: {args.get('body')}"
                        ),
                        "metadata": {
                            "source": "Email",
                            "recipient": args.get("to"),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    },
                }
                new_nodes.append(node)

            elif function_name == "query_perplexity":
                result_text = query_perplexity(perplexity_client, args.get("query", ""))
                node = {
                    "id": str(uuid.uuid4()),
                    "node_class": "report",
                    "content": {
                        "text": result_text,
                        "metadata": {
                            "source": "Perplexity",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    },
                }
                new_nodes.append(node)
                result = result_text

            elif function_name == "video_analysis":
                result = video_analysis(args.get("video_url", ""))

            elif function_name == "create_node":
                print(f"Creating node '{args.get('node_class')}' with text: {args.get('text')}")
                node_class = args.get("node_class")
                text = args.get("text")
                node = {
                    "id": str(uuid.uuid4()),
                    "node_class": node_class,
                    "content": {
                        "text": text,
                        "metadata": {
                            "source": "LLM",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    },
                }
                new_nodes.append(node)
                result = f"Node '{node_class}' created."

            elif function_name == "create_edge":
                print(f"Creating edge from {args.get('from_id')} to {args.get('to_id')}")
                from_id = args.get("from_id")
                to_id = args.get("to_id")
                edge = {
                    "id": str(uuid.uuid4()),
                    "from": from_id,
                    "to": to_id,
                }
                new_edges.append(edge)
                result = f"Edge from {from_id} to {to_id} created."

            else:
                result = "Function not recognized."

            # Append tool response corresponding to this tool_call_id.
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": result}
            )

        # After all tool calls are processed, get the final assistant message.
        final_response = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools, temperature=0.7
        )
        assistant_message = final_response.choices[0].message.content
    else:
        assistant_message = message.content

    # Ensure assistant_message is not None before processing
    assistant_message = assistant_message if assistant_message is not None else ""

    # If the assistant asks a query (using "QUERY:"), prompt the user further.
    if "QUERY:" in assistant_message:
        parts = assistant_message.split("QUERY:")
        assistant_text = parts[0].strip()
        query_text = parts[1].strip()
        assistant_message = (
            assistant_text + "\nPlease provide additional info: " + query_text
        )
    # print edges
    print(f"Edges: {new_edges}")
    print(f"Nodes: {new_nodes}")
    return {
        "assistant_message": assistant_message,
        "new_nodes": new_nodes,
        "new_edges": new_edges,
    }

if __name__ == "__main__":
    nodes = []
    active_node = None
    init_agent(nodes, active_node)


# tools = [
#     {
#         "type": "function",
#         "function": {
#             "name": "send_email",
#             "description": "Send an email to a given recipient with a subject and message.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "to": {
#                         "type": "string",
#                         "description": "The recipient email address.",
#                     },
#                     "subject": {
#                         "type": "string",
#                         "description": "The email subject line.",
#                     },
#                     "body": {
#                         "type": "string",
#                         "description": "The body of the email.",
#                     },
#                 },
#                 "required": ["to", "subject", "body"],
#                 "additionalProperties": False,
#             },
#             "strict": True,
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "query_perplexity",
#             "description": "Query the Perplexity API with a research query.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "query": {
#                         "type": "string",
#                         "description": "The research query.",
#                     }
#                 },
#                 "required": ["query"],
#                 "additionalProperties": False,
#             },
#             "strict": True,
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "video_analysis",
#             "description": "Simulate video analysis steps for a provided video URL.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "video_url": {
#                         "type": "string",
#                         "description": "The URL of the video to analyze.",
#                     }
#                 },
#                 "required": ["video_url"],
#                 "additionalProperties": False,
#             },
#             "strict": True,
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "create_node",
#             "description": "Create a new research node in the graph.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "node_class": {
#                         "type": "string",
#                         "description": "The class of the node (e.g., heading, tweet, report, video).",
#                     },
#                     "text": {
#                         "type": "string",
#                         "description": "The content text for the node.",
#                     },
#                 },
#                 "required": ["node_class", "text"],
#                 "additionalProperties": False,
#             },
#             "strict": True,
#         },
#     },
#     {
#         "type": "function",
#         "function": {
#             "name": "create_edge",
#             "description": "Create an edge between two nodes in the graph.",
#             "parameters": {
#                 "type": "object",
#                 "properties": {
#                     "from_id": {
#                         "type": "string",
#                         "description": "The source node id.",
#                     },
#                     "to_id": {
#                         "type": "string",
#                         "description": "The target node id.",
#                     },
#                 },
#                 "required": ["from_id", "to_id"],
#                 "additionalProperties": False,
#             },
#             "strict": True,
#         },
#     },
# ]