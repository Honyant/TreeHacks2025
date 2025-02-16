import uuid
import json
import logging
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import imaplib
import email
from email.header import decode_header
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from openai import OpenAI
from external_functions import (
    query_perplexity,
    query_rag,
    call_phone_number,
    send_email,
)
from utils import *
import schemas

load_dotenv()
verbose = False
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
perplexity_client = OpenAI(
    api_key=os.getenv("PERPLEXITY_API_KEY"), base_url="https://api.perplexity.ai"
)


def init_agent(nodes: list[schemas.NodeV2], active_node: str):
    brief = load_brief("demo/ukraine_brief.txt")
    init_brief_prompt = """
    You are helping create a root node for a research project. Given a project brief:
    1. Generate a 5-word title that captures the key focus
    2. Write a concise summary (max 200 words) that captures the essence of the investigation
    Format the response as JSON with "title" and "content" fields.
    """

    messages = [
        {"role": "system", "content": init_brief_prompt},
        {"role": "user", "content": f"Project brief:\n{brief}"},
    ]

    print("Initializing agent")
    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, response_format={"type": "json_object"}
    )

    response_content = response.choices[0].message.content
    parsed_response = schemas.ModelOutput.model_validate(json.loads(response_content))

    root_node_id = create_node(
        nodes,
        parsed_response.title,
        "root",
        parsed_response.content,
        "brief",
        datetime.now(),
    )
    if verbose:
        print(f"Root node created with id: {root_node_id}")
    # print content
    try:
        root_node = get_node_by_id(nodes, root_node_id)
    except Exception as e:
        print(f"Error getting node by id: {e}")
        root_node = None
    if verbose:
        print(f"node_content: {root_node.content}")
    return root_node_id


def execute_mode_i(nodes: list[schemas.NodeV2], active_node: str, collection):
    """
    Executes mode I of the research agent, which expands knowledge by using
    tools to gather information.
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
        {"role": "system", "content": mode_i},
        {
            "role": "user",
            "content": f"""

        The entire research graph:
        {nodes_to_string(nodes)}

        The current research node:
        Title: {current_node_name}
        Content: {current_node_content}

         Generate a list of call functions to be executed to gather information.
         """,
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, tools=mode_i_tools, temperature=0.7
    )
    message = response.choices[0].message
    new_nodes = []

    if hasattr(message, "tool_calls") and message.tool_calls:
        messages.append(message)
        for tool_call in message.tool_calls:
            if tool_call.function.name == "search":
                args = json.loads(tool_call.function.arguments)
                result = query_perplexity(perplexity_client, args["query"])
                new_node_id = create_node(
                    nodes=nodes,
                    name=args["name"],
                    type="search",
                    content=result,
                    source="perplexity_search",
                    timestamp=datetime.now(),
                )
                current_node.children.append(new_node_id)
                new_nodes.append(new_node_id)
            elif tool_call.function.name == "retrieve":
                args = json.loads(tool_call.function.arguments)
                result = query_rag(args.get("query", ""), collection)
                new_node_id = create_node(
                    nodes=nodes,
                    name=args["name"],
                    type="file",
                    content=result,
                    source="rag",
                    timestamp=datetime.now(),
                )
                current_node.children.append(new_node_id)
                new_nodes.append(new_node_id)
            elif tool_call.function.name == "email":
                args = json.loads(tool_call.function.arguments)
                result = send_email(args["recipient"], args["subject"], args["message"])
                new_node_id = create_node(
                    nodes=nodes,
                    name=args["name"],
                    type="email",
                    content=args["message"] + "\n" + result,
                    source="email",
                    timestamp=datetime.now(),
                )
                current_node.children.append(new_node_id)
                new_nodes.append(new_node_id)
            elif tool_call.function.name == "phone":
                args = json.loads(tool_call.function.arguments)
                result = call_phone_number("+16501234567", args["topic"])
                new_node_id = create_node(
                    nodes=nodes,
                    name=args["name"],
                    type="call",
                    content=result,
                    source="call",
                    timestamp=datetime.now(),
                )
                current_node.children.append(new_node_id)
                new_nodes.append(get_node_by_id(nodes, new_node_id))
            elif tool_call.function.name == "ask":
                args = json.loads(tool_call.function.arguments)
                new_node_id = create_node(
                    nodes=nodes,
                    name=args["name"],
                    type="question",
                    content=args["question"],
                    source="question",
                    timestamp=datetime.now(),
                )
                current_node.children.append(new_node_id)
                new_nodes.append(new_node_id)

    if verbose:
        print_nodes(nodes)
    return new_nodes


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
        {
            "role": "user",
            "content": f"""

         The current research node:
         Title: {current_node_name}
         Content: {current_node_content}

         Generate relevant insights and create new nodes.
""",
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, tools=mode_ii_tools, temperature=0.7
    )

    message = response.choices[0].message
    new_nodes = []

    if hasattr(message, "tool_calls") and message.tool_calls:
        messages.append(message)
        for tool_call in message.tool_calls:
            if tool_call.function.name == "create_node":
                args = json.loads(tool_call.function.arguments)
                child_id = create_node(
                    nodes=nodes,
                    name=args["name"],
                    type=args["type"],
                    content=args["content"],
                    source="mode_ii",
                    timestamp=datetime.now(),
                )
                new_nodes.append(child_id)
                update_node_children(nodes, active_node, child_id)
                if verbose:
                    print(f"Created new node: {args['name']}")

    if verbose:
        print_nodes(nodes)
    if verbose:
        print(nodes)
    return new_nodes


def execute_mode_iii(nodes: list[schemas.NodeV2], active_node: str, user_message: str):
    """
    Executes mode III of the research agent, which expands knowledge by analyzing
    the situation and generating new insights for the active node.
    """
    if not active_node:
        print("No active node selected")
        return

    current_node = get_node_by_id(nodes, active_node)
    if not current_node:
        print(f"Could not find active node with id: {active_node}")
        return


def process_chat(
    user_message: str, node_id: str, nodes: list[schemas.NodeV2]
) -> schemas.NodeV2:
    """
    Process a chat message and create a new node based on it.

    Args:
        user_message: The message from the user
        node_id: ID of the node this chat is associated with
        nodes: List of all nodes in the graph

    Returns:
        The newly created node
    """
    # Find the parent node if one was specified
    parent_node = get_node_by_id(nodes, node_id) if node_id else None

    # Create a response node
    response_node_id = create_node(
        nodes=nodes,
        name="Chat Response",
        type="text",
        content=user_message,
        source="chat",
        timestamp=datetime.now(),
    )

    # If there was a parent node, update its children
    if parent_node:
        update_node_children(nodes, parent_node.id, response_node_id)

    # Return the newly created node
    return get_node_by_id(nodes, response_node_id)


def check_for_replies():
    """
    Periodically checks for new emails from the last 2 minutes, then processes replies.
    """
    # Connect to the email server
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASSWORD"))

    # Select the mailbox you want to check
    mail.select("inbox")

    while True:
        print("Checking for new emails...")
        # Calculate the time 2 minutes ago, ensuring it's timezone-aware (UTC)
        two_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=2)
        # Format the date for the IMAP search (day-based only)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        date_str = yesterday.strftime("%d-%b-%Y")

        # Search for emails "since" that day (IMAP is day-based, so we still need to manually filter times below)
        status, messages = mail.search(None, f'(SINCE "{date_str}")')
        if status != "OK":
            logging.warning("IMAP search failed or returned no messages.")
            time.sleep(10)
            continue

        email_ids = messages[0].split()
        if not email_ids:
            logging.info("No new emails found in the last 2 minutes (day-based check).")
            time.sleep(10)
            continue

        print(f"Found {len(email_ids)} new emails.")

        for email_id in email_ids:
            # Fetch the email by ID
            fetch_status, msg_data = mail.fetch(email_id, "(RFC822)")
            if fetch_status != "OK":
                logging.warning(f"Error fetching email with ID: {email_id}")
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    # Get the email date
                    email_date = email.utils.parsedate_to_datetime(msg["Date"])

                    # Convert email_date to UTC for consistent comparison.
                    if email_date.tzinfo is None:
                        email_date = email_date.replace(tzinfo=timezone.utc)
                    else:
                        email_date = email_date.astimezone(timezone.utc)

                    print(f"Email date: {email_date}")
                    print(f"Two minutes ago: {two_minutes_ago}")
                    if email_date > two_minutes_ago:
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")

                        # Check if the email is a reply using multiple criteria
                        is_reply = "In-Reply-To" in msg or "References" in msg
                        is_reply = is_reply or subject.lower().startswith("re:")

                        if is_reply:
                            print(f"Subject: {subject}")
                            logging.info(f"New reply detected. Subject: {subject}")
                            process_reply(msg)

        # Wait for a while before checking again
        time.sleep(10)


def process_reply(msg):
    """
    Process the reply by extracting its content and updating the relevant node.
    """
    # Extract the email content
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                body = part.get_payload(decode=True).decode(errors="replace")
                break
    else:
        body = msg.get_payload(decode=True).decode(errors="replace")

    logging.info(f"Reply received: {body}")
    # Update your node with the reply content
    # Example: store_reply_in_node(body)
    # (Implement your own logic here as needed.)


def send_email(to: str, subject: str, body: str) -> str:
    """
    Sends an email via SMTP using configuration details provided via environment variables.

    Environment Variables:
      - SMTP_HOST: SMTP server address (default: smtp.gmail.com)
      - SMTP_PORT: SMTP server port (default: 587)
      - SMTP_USER: SMTP username/email (default: your-email@gmail.com)
      - SMTP_PASSWORD: SMTP password (App Password for Gmail)
    """
    # Load SMTP configuration from environment variables.
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))
    smtp_user = os.environ.get("SMTP_USER", "your-email@gmail.com")
    smtp_password = os.environ.get("SMTP_PASSWORD", "your-app-password")

    # Create the email message.
    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        # Connect to the SMTP server, start TLS, login, and send the email.
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to, msg.as_string())
        server.quit()
        print(f"[Email] Sent email to {to} with subject '{subject}'.")
        return "Email sent."
    except Exception as e:
        print(f"[Email] Error sending email: {e}")
        return f"Failed to send email: {e}"


# if __name__ == "__main__":
#     # Start the email listener in a background thread
#     from threading import Thread

#     listener_thread = Thread(target=check_for_replies, daemon=True)
#     listener_thread.start()

#     # Simulate sending an email via the engine
#     print("Sending test email through engine...")
#     email_result = send_email(
#         to=os.environ.get("TEST_EMAIL", "asstinbrown@gmail.com"),
#         subject="Engine Test Email",
#         body="This is a test email sent from the engine for asynchronous reply processing.",
#     )
#     print(email_result)

#     # Keep the main thread alive to allow asynchronous email checking
#     try:
#         while True:
#             time.sleep(5)
#     except KeyboardInterrupt:
#         print("Shutting down.")


def process_chat_message(user_message: str, node_id: str, nodes, chat_messages):
    """
    Process a chat message and create a new node based on it.
    Uses OpenAI's tool use API to generate an appropriate response node.

    Args:
        user_message: The message from the user
        node_id: ID of the node this chat is associated with
        nodes: List of all nodes in the graph

    Returns:
        The newly created node
    """
    transcript = ""
    for msg in chat_messages:
        transcript += f"{msg.role}: {msg.message}\n"
    # Find the parent node if one was specified
    parent_node = get_node_by_id(nodes, node_id) if node_id else None

    # Call OpenAI API with function calling enabled
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": 'You have access to the following tools: ["create_node"]',
            },
            {"role": "user", "content": transcript},
            {"role": "assistant", "content": f"The user is asking you about this node: {parent_node.content}"},
            {"role": "user", "content": user_message},
        ],
        tools=mode_ii_tools,
        temperature=0.7,
    )

    message = response.choices[0].message

    # Process the tool calls if any
    if hasattr(message, "tool_calls") and message.tool_calls:
        for tool_call in message.tool_calls:
            if tool_call.function.name == "create_node":
                args = json.loads(tool_call.function.arguments)
                response_node_id = create_node(
                    nodes=nodes,
                    name=args["name"],
                    type=args["type"],
                    content=args["content"],
                    source="chat",
                    timestamp=datetime.now(),
                )

                # If there was a parent node, update its children
                if parent_node:
                    update_node_children(nodes, parent_node.id, response_node_id)

                return get_node_by_id(nodes, response_node_id)

    # Fallback: create a simple response node if no tool calls
    response_node_id = create_node(
        nodes=nodes,
        name="Chat Response",
        type="text",
        content=message.content or user_message,
        source="chat",
        timestamp=datetime.now(),
    )

    # If there was a parent node, update its children
    if parent_node:
        update_node_children(nodes, parent_node.id, response_node_id)

    return get_node_by_id(nodes, response_node_id)
