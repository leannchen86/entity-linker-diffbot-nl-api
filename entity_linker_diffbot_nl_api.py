from openai import OpenAI
import json
import requests
import os

os.environ["OPENAI_API_KEY"] = 'openai-key'

client = OpenAI()

FIELDS = "entities"
HOST = "nl.diffbot.com"
TOKEN = "diffbot-token" 

import requests

def get_request(payload):
    res = requests.post("https://{}/v1/?fields={}&token={}".format(HOST, FIELDS, TOKEN), json=payload)
    ret = None
    try:
        ret = res.json()
    except:
        print("Bad response: " + res.text)
        print(res.status_code)
        print(res.headers)
    return ret

def get_entity_types_diffbot(res):
    entity_types = []
    if res['entities'] == []:
        entity_types = "No valid entity type found from the answer."
    else:
        answer_name = res['entities'][0]['name']
        answer_types = res['entities'][0]['allTypes']
        for i in range(len(answer_types)): 
            entity_type = answer_types[i]['name']
            entity_types.append(entity_type)
        
    return entity_types

def type_evaluator_by_llm(question):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant who determines the correct entity type that the answer of the question should belongs to. Possible entity types are organization, person, product, country, city, article. And if the question is a yes-or-no type of question, answer: yes/no type. Yes/No type questions start with: Is, Was, Do, Did, etc."},
            {"role": "user", "content": question},
        ]
    )
    answer = response.choices[0].message.content
    question_type = answer
    return question_type

def entity_linker(answer_vector, question):
    if answer_vector.lower() == "none":
        return "The entity type of the answer should be: None", "Entity type(s) of the answer: None", "entity type matched!"
    
    # fact-check validity of vector-based answer via Diffbot Natural Language API
    type_to_be_checked = answer_vector
    content = "Please verify the type of: " + type_to_be_checked
    
    res = get_request({
        "content": content,
        "lang": "en",
        "format": "plain text with title"
    })
    
    entity_list_diffbot = get_entity_types_diffbot(res)
    question_type = type_evaluator_by_llm(question)
    correct_question_type = "The entity type of the answer should be: " + type_evaluator_by_llm(question)
    
    if entity_list_diffbot != [] and "yes" not in question_type.lower():
        type_matches = any(question_type.lower() in entity.lower() for entity in entity_list_diffbot)
        original_answer_type = "Entity type(s) of the answer: "
        if isinstance(entity_list_diffbot, list):
            original_answer_type += ', '.join(entity_list_diffbot)
        else:
            original_answer_type += entity_list_diffbot
            
        if type_matches:
            type_status = "entity type matched!"
        else:
            type_status = "entity type not matched!"

    elif "yes" or "no" in question_type.lower():
        original_answer_type = "Entity type(s) of the answer: " + "yes/no type"
        type_status = "entity type not required for the answer!"
        
    else:
        original_answer_type = "Entity type(s) of the answer: invalid."
        type_status = "entity type not matched!"
        
    return correct_question_type, original_answer_type, type_status
