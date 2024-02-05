#!C:\Program Files\Python311\python.exe

print("Program Starting!")
from pinecone import Pinecone, PodSpec
from config import * #define PINECONE_API_KEY in this file

OBJECTIVE = "Do cutting-edge research on AI as a solution to climate change."
YOUR_FIRST_TASK = "Develop a task list. Do not include any other text."

from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L12-v2")

#Set API Keys
OPENAI_API_KEY = "" #we no longer need closedAI
PINECONE_ENVIRONMENT =  "us-west1-gcp" #Pinecone Environment (eg. "us-east1-gcp")

import time
from g4f import ChatCompletion
from g4f import Provider
from collections import deque
from typing import Dict, List
print("Imports Finished!")

#current requirements: g4f, pinecone, sentence_transformers

#Set Variables
YOUR_TABLE_NAME = "test-table"

#Print OBJECTIVE
print("\033[96m\033[1m"+"\n*****OBJECTIVE*****\n"+"\033[0m\033[0m")
print(OBJECTIVE)

# Configure OpenAI and Pinecone
#openai.api_key = OPENAI_API_KEY
pinecone = Pinecone(api_key=PINECONE_API_KEY)

# Create Pinecone index
table_name = YOUR_TABLE_NAME
dimension = 384
metric = "cosine"
pod_type = "p1" #specifices storage requirements for pinecone hosting based on vector dimensions, query rate, and metadata size
if table_name not in pinecone.list_indexes().names():
    pinecone.create_index(name=table_name,
                          dimension=dimension,
                          metric=metric,
                          spec = PodSpec(
                          environment="gcp-starter"))

# Connect to the index
index = pinecone.Index(table_name)

# Task list
task_list = deque([])

def add_task(task: Dict):
    task_list.append(task)

def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return model.encode([text])[0]

def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str]):
    prompt = f"You are an task creation agent that uses the result of an LLM-based execution agent to create new tasks with the following objective: {objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Make sure the tasks can be completed by an LLM agent. Return the tasks as an array."
    while True:
        try:
            response = ChatCompletion.create(
            model="gpt-4",
            provider=Provider.Bing,
            tone = "Precise",
            messages=[{"role": "user", "content": prompt}],
            )
            break
        except Exception as e:
            print("gp4 ran into error")
            print(e)
    print("Tasks created successfully!")
    new_tasks = response.strip().split('\n')
    task_dict = [{"task_name": task_name} for task_name in new_tasks]
    print(task_dict)
    return task_dict

def prioritization_agent(this_task_id:int):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id)+1
    prompt = f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{OBJECTIVE}. Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}. Do not include any other text."""
    response = ChatCompletion.create(
      model="gpt-4",
      provider=Provider.Bing,
      tone = "Precise",
      messages=[{"role": "user", "content": prompt}],
    )
    new_tasks = response.strip().split('\n')
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})

def execution_agent(objective:str,task: str) -> str:
    #context = context_agent(index="quickstart", query="my_search_query", n=5)
    context=context_agent(query=task, n=3)
    try:
        context = context[0]
    except:
        context = {'task':"No previously completed tasks",'result':"No previous results"}
    print("\n*******RELEVANT CONTEXT******\n")
    print(context)
    prompt = f"You are an execution agent on a team tasked with the following objective: '{objective}'. The most relevant tasks that have already been completed are: '{context['task']}'. Here are the results of those tasks '{context['result']}'. Complete your task: {task}\nResponse:"
    while True:
        try:
            response = ChatCompletion.create(
            model="gpt-4",
            provider=Provider.Bing,
            tone = "Precise",
            messages=[{"role": "user", "content": prompt}],
            )
            break
        except Exception as e:
            print("gp4 ran into error")
            print(e)
    return response.strip()

def context_agent(query: str, n: int):
    query_embedding = get_ada_embedding(query)
    results = index.query(vector=query_embedding.tolist(), top_k=n,
    include_metadata=True)
    #print("***** RESULTS *****")
    #print(results)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
    return [{'task':str(item.metadata['task']),'result':str(item.metadata['result'])} for item in sorted_results]

# Add the first task
first_task = {
    "task_id": 1,
    "task_name": YOUR_FIRST_TASK
}

add_task(first_task)
# Main loop
task_id_counter = 1
while True:
    if task_list:
        # Print the task list
        print("\033[95m\033[1m"+"\n*****TASK LIST*****\n"+"\033[0m\033[0m")
        for t in task_list:
            print(str(t['task_id'])+": "+t['task_name'])

        # Step 1: Pull the first task
        task = task_list.popleft()
        print("\033[92m\033[1m"+"\n*****NEXT TASK*****\n"+"\033[0m\033[0m")
        print(str(task['task_id'])+": "+task['task_name'])

        # Send to execution function to complete the task based on the context
        result = execution_agent(OBJECTIVE,task["task_name"])
        this_task_id = int(task["task_id"])
        print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
        print(result)

        # Step 2: Enrich result and store in Pinecone
        enriched_result = {'data': result}  # This is where you should enrich the result if needed
        result_id = f"result_{task['task_id']}"
        vector = enriched_result['data']  # extract the actual result from the dictionary
        index.upsert([(result_id, get_ada_embedding(task['task_name']),{"task":task['task_name'],"result":result})])

    # Step 3: Create new tasks and reprioritize task list
    new_tasks = task_creation_agent(OBJECTIVE,enriched_result, task["task_name"], [t["task_name"] for t in task_list])

    for new_task in new_tasks:
        task_id_counter += 1
        new_task.update({"task_id": task_id_counter})
        add_task(new_task)
    prioritization_agent(this_task_id)

time.sleep(1)  # Sleep before checking the task list again
