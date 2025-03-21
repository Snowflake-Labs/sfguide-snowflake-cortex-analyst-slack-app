from typing import Any, Dict, List
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import snowflake.connector
import requests
import pandas as pd
from snowflake.core import Root
from dotenv import load_dotenv
import matplotlib
import time
import matplotlib.pyplot as plt 
from cortex_chat import CortexChat

matplotlib.use('Agg')
load_dotenv()

# Environment Variables
USER = os.getenv("USER")
ACCOUNT = os.getenv("ACCOUNT")
ANALYST_ENDPOINT = os.getenv("ANALYST_ENDPOINT")
RSA_PRIVATE_KEY_PATH = os.getenv("RSA_PRIVATE_KEY_PATH")
SUPPORT_TICKETS_SEMANTIC_MODEL = os.getenv("SUPPORT_TICKETS_SEMANTIC_MODEL")
SUPPLY_CHAIN_SEMANTIC_MODEL = os.getenv("SUPPLY_CHAIN_SEMANTIC_MODEL")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
ENABLE_CHARTS = True
DEBUG = False

# Initialize Slack App
app = App(token=SLACK_BOT_TOKEN)

# Initialize Snowflake and CortexClient
conn = snowflake.connector.connect(
    user=USER,
    authenticator="SNOWFLAKE_JWT",
    private_key_file=RSA_PRIVATE_KEY_PATH,
    account=ACCOUNT
)
cortex_chat = CortexChat(ACCOUNT, USER, RSA_PRIVATE_KEY_PATH, ANALYST_ENDPOINT, SUPPORT_TICKETS_SEMANTIC_MODEL, SUPPLY_CHAIN_SEMANTIC_MODEL)

Root = Root(conn)

@app.message("hello")
def message_hello(message, say):
    say(f"Hey there <@{message['user']}>!")
    say(text="Let's BUILD", blocks=[
        {"type": "header", "text": {"type": "plain_text", "text": ":snowflake: Let's BUILD!"}}
    ])

@app.event("message")
def handle_message_events(ack, body, say):
    ack()
    process_analyst_message(body['event']['text'], say)

@app.command("/asksnowflake")
def ask_cortex(ack, body, say):
    ack()
    process_analyst_message(body['text'], say)

def process_analyst_message(prompt, say) -> Any:
    say_question(prompt, say)
    response = cortex_chat.query_cortex_analyst(prompt)
    display_analyst_content(response["message"]["content"], say)

def say_question(prompt, say):
    say(text=f"Question: {prompt}", blocks=[
        {"type": "header", "text": {"type": "plain_text", "text": f"Question: {prompt}"}},
        {"type": "divider"},
        {"type": "section", "text": {"type": "plain_text", "text": "Snowflake Cortex Analyst is generating a response. Please wait..."}},
        {"type": "divider"}
    ])

def display_analyst_content(content: List[Dict[str, str]], say):
    for item in content:
        if item["type"] == "sql":
            say(text="Generated SQL", blocks=[
                {"type": "rich_text", "elements": [{"type": "rich_text_preformatted", "elements": [{"type": "text", "text": item['statement']}]}]}
            ])
            df = pd.read_sql(item["statement"], conn)
            say(text="Answer:", blocks=[
                {"type": "rich_text", "elements": [{"type": "rich_text_preformatted", "elements": [{"type": "text", "text": df.to_string()}]}]}
            ])
            if ENABLE_CHARTS and len(df.columns) > 1:
                try:
                    chart_img_url = plot_chart(df)
                    if chart_img_url:
                        say(text="Chart", blocks=[
                            {"type": "image", "title": {"type": "plain_text", "text": "Chart"}, "block_id": "image", "slack_file": {"url": chart_img_url}, "alt_text": "Chart"}
                        ])
                except Exception as e:
                    print(f"Warning: Unable to generate chart - {e}")
        elif item["type"] == "suggestions":
            suggestions = "\n- ".join(item['suggestions'])
            say(text=f"You may try these suggested questions:\n- {suggestions}")

def plot_chart(df):
    plt.figure(figsize=(10, 6))
    plt.pie(df[df.columns[1]], labels=df[df.columns[0]], autopct='%1.1f%%', startangle=90)
    plt.axis('equal')
    file_path = 'chart.jpg'
    plt.savefig(file_path, format='jpg')
    file_upload_url = app.client.files_getUploadURLExternal(filename=file_path, length=os.path.getsize(file_path))
    file_id = file_upload_url['file_id']
    with open(file_path, 'rb') as f:
        requests.post(file_upload_url['upload_url'], files={'file': f})
    response = app.client.files_completeUploadExternal(files=[{"id": file_id, "title": "chart"}])
    time.sleep(2)
    return response['files'][0]['permalink'] if response.get('files') else None

if __name__ == "__main__":
    SocketModeHandler(app, SLACK_APP_TOKEN).start()



# from typing import Any, Dict, List, Optional
# import os
# from slack_bolt import App
# from slack_bolt.adapter.socket_mode import SocketModeHandler
# import snowflake.connector
# import requests
# import pandas as pd
# from snowflake.core import Root
# import generate_jwt
# from dotenv import load_dotenv
# import json
# import io
# import matplotlib
# import matplotlib.pyplot as plt 
# import time

# matplotlib.use('Agg')
# load_dotenv()

# USER = os.getenv("USER")
# ACCOUNT = os.getenv("ACCOUNT")
# DATABASE = os.getenv("DATABASE")
# SCHEMA = os.getenv("SCHEMA")
# PASSWORD = os.getenv("PASSWORD")
# ANALYST_ENDPOINT = os.getenv("ANALYST_ENDPOINT")
# RSA_PRIVATE_KEY_PATH = os.getenv("RSA_PRIVATE_KEY_PATH")
# STAGE = os.getenv("SEMANTIC_MODEL_STAGE")
# FILE = os.getenv("SEMANTIC_MODEL_FILE")
# SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN_SF")
# SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN_SF")
# JWT = None
# ENABLE_CHARTS = True
# DEBUG = True

# # Initializes app
# app = App(token=SLACK_BOT_TOKEN)
# messages = []

# @app.message("hello")
# def message_hello(message, say):
#     say(f"Hey there <@{message['user']}>!")
#     say(
#         text = "Let's BUILD",
#         blocks = [
#             {
#                 "type": "header",
#                 "text": {
#                     "type": "plain_text",
#                     "text": f":snowflake: Let's BUILD!",
#                 }
#             },
#         ]                
#     )

# @app.event("message")
# def handle_message_events(ack, body, say):
#     ack()
#     prompt = body['event']['text']
#     process_analyst_message(prompt, say)

# @app.command("/asksnowflake")
# def ask_cortex(ack, body, say):
#     ack()
#     prompt = body['text']
#     process_analyst_message(prompt, say)

# def process_analyst_message(prompt, say) -> Any:
#     say_question(prompt, say)
#     response = query_cortex_analyst(prompt)
#     content = response["message"]["content"]
#     display_analyst_content(content, say)

# def say_question(prompt,say):
#     say(
#         text = "Question:",
#         blocks = [
#             {
#                 "type": "header",
#                 "text": {
#                     "type": "plain_text",
#                     "text": f"Question: {prompt}",
#                 }
#             },
#         ]                
#     )
#     say(
#         text = "Snowflake Cortex Analyst is generating a response",
#         blocks=[
#             {
#                 "type": "divider"
#             },
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "plain_text",
#                     "text": "Snowflake Cortex Analyst is generating a response. Please wait...",
#                 }
#             },
#             {
#                 "type": "divider"
#             },
#         ]
#     )

# def query_cortex_analyst(prompt) -> Dict[str, Any]:
#     print(JWT)
#     request_headers = {
#         "X-Snowflake-Authorization-Token-Type": "KEYPAIR_JWT",
#         "Content-Type": "application/json",
#         "Accept": "application/json",
#         "Authorization": f"Bearer {JWT}",
#     }
#     request_body = {
#         "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}],
#         "semantic_model_file": f"@{DATABASE}.{SCHEMA}.{STAGE}/{FILE}",
#     }

#     resp = requests.post(
#         url=f"{ANALYST_ENDPOINT}",
#         headers=request_headers,
#         json=request_body,
#     )

#     if resp.status_code == 401:  # Unauthorized - likely expired JWT
#         print("JWT has expired. Generating new JWT...")
#         # Generate new token
#         JWT = generate_jwt.JWTGenerator(ACCOUNT,USER,RSA_PRIVATE_KEY_PATH).get_token()
#         # Retry the request with the new token
#         print("New JWT generated. Sending new request to Cortex Agents API. Please wait...")
#         resp = requests.post(
#             url=f"{ANALYST_ENDPOINT}",
#             headers=request_headers,
#             json=request_body,
#         )

#     request_id = resp.headers.get("X-Snowflake-Request-Id")
#     if resp.status_code == 200:
#         if DEBUG:
#             print(resp.text)
#         return {**resp.json(), "request_id": request_id}  
#     else:
#         raise Exception(
#             f"Failed request (id: {request_id}) with status {resp.status_code}: {resp.text}"
#         )

# def display_analyst_content(
#     content: List[Dict[str, str]],
#     say=None
# ) -> None:
#     if DEBUG:
#         print(content)
#     for item in content:
#         if item["type"] == "sql":
#             say(
#                 text = "Generated SQL",
#                 blocks = [
#                     {
#                         "type": "rich_text",
#                         "elements": [
#                             {
#                                 "type": "rich_text_preformatted",
#                                 "elements": [
#                                     {
#                                         "type": "text",
#                                         "text": f"{item['statement']}"
#                                     }
#                                 ]
#                             }
#                         ]
#                     }
#                 ]
#             )
#             df = pd.read_sql(item["statement"], CONN)
#             say(
#                 text = "Answer:",
#                 blocks=[
#                     {
#                         "type": "rich_text",
#                         "elements": [
#                             {
#                                 "type": "rich_text_quote",
#                                 "elements": [
#                                     {
#                                         "type": "text",
#                                         "text": "Answer:",
#                                         "style": {
# 								            "bold": True
# 							            }
#                                     }
#                                 ]
#                             },
#                             {
#                                 "type": "rich_text_preformatted",
#                                 "elements": [
#                                     {
#                                         "type": "text",
#                                         "text": f"{df.to_string()}"
#                                     }
#                                 ]
#                             }
#                         ]
#                     }
#                 ]
#             )
#             if ENABLE_CHARTS and len(df.columns) > 1:
#                 chart_img_url = None
#                 try:
#                     chart_img_url = plot_chart(df)
#                 except Exception as e:
#                     error_info = f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}"
#                     print(f"Warning: Data likely not suitable for displaying as a chart. {error_info}")                
#                 if chart_img_url is not None:
#                     say(
#                         text = "Chart",
#                         blocks=[
#                             {
#                                 "type": "image",
#                                 "title": {
#                                     "type": "plain_text",
#                                     "text": "Chart"
#                                 },
#                                 "block_id": "image",
#                                 "slack_file": {
#                                     "url": f"{chart_img_url}"
#                                 },
#                                 "alt_text": "Chart"
#                             }
#                         ]
#                     )
#         elif item["type"] == "text":
#             say(
#                 text = "Answer:",
#                 blocks = [
#                     {
#                         "type": "rich_text",
#                         "elements": [
#                             {
#                                 "type": "rich_text_quote",
#                                 "elements": [
#                                     {
#                                         "type": "text",
#                                         "text": f"{item['text']}"
#                                     }
#                                 ]
#                             }
#                         ]
#                     }
#                 ]
#             )
#         elif item["type"] == "suggestions":
#             suggestions = "You may try these suggested questions: \n\n- " + "\n- ".join(item['suggestions']) + "\n\nNOTE: There's a 150 char limit on Slack messages so alter the questions accordingly."
#             say(
#                 text = "Suggestions:",
#                 blocks = [
#                     {
#                         "type": "rich_text",
#                         "elements": [
#                             {
#                                 "type": "rich_text_preformatted",
#                                 "elements": [
#                                     {
#                                         "type": "text",
#                                         "text": f"{suggestions}"
#                                     }
#                                 ]
#                             }
#                         ]
#                     }
#                 ]
#             )               

# def plot_chart(df):
#     plt.figure(figsize=(10, 6), facecolor='#333333')

#     # plot pie chart with percentages, using dynamic column names
#     plt.pie(df[df.columns[1]], 
#             labels=df[df.columns[0]], 
#             autopct='%1.1f%%', 
#             startangle=90, 
#             colors=['#1f77b4', '#ff7f0e'], 
#             textprops={'color':"white",'fontsize': 16})

#     # ensure equal aspect ratio
#     plt.axis('equal')
#     # set the background color for the plot area to dark as well
#     plt.gca().set_facecolor('#333333')   
#     plt.tight_layout()

#     # save the chart as a .jpg file
#     file_path_jpg = 'pie_chart.jpg'
#     plt.savefig(file_path_jpg, format='jpg')
#     file_size = os.path.getsize(file_path_jpg)

#     # upload image file to slack
#     file_upload_url_response = app.client.files_getUploadURLExternal(filename=file_path_jpg,length=file_size)
#     if DEBUG:
#         print(file_upload_url_response)
#     file_upload_url = file_upload_url_response['upload_url']
#     file_id = file_upload_url_response['file_id']
#     with open(file_path_jpg, 'rb') as f:
#         response = requests.post(file_upload_url, files={'file': f})

#     # check the response
#     img_url = None
#     if response.status_code != 200:
#         print("File upload failed", response.text)
#     else:
#         # complete upload and get permalink to display
#         response = app.client.files_completeUploadExternal(files=[{"id":file_id, "title":"chart"}])
#         if DEBUG:
#             print(response)
#         img_url = response['files'][0]['permalink']
#         time.sleep(2)
    
#     return img_url

# def init():
#     conn,jwt = None,None
#     conn = snowflake.connector.connect(
#         user=USER,
#         authenticator="SNOWFLAKE_JWT",
#         private_key_file=RSA_PRIVATE_KEY_PATH,
#         account=ACCOUNT
#     )
#     jwt = generate_jwt.JWTGenerator(ACCOUNT,USER,RSA_PRIVATE_KEY_PATH).get_token()
#     print(">>>>>>>>>> Init complete")
#     return conn,jwt

# # Start app
# if __name__ == "__main__":
#     CONN,JWT = init()
#     if not CONN.rest.token:
#         print("Error: Failed to connect to Snowflake! Please check your Snowflake user, password, and account environment variables and try again.")
#         quit()

#     Root = Root(CONN)
#     SocketModeHandler(app, SLACK_APP_TOKEN).start()
