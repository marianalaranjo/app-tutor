import streamlit as st
import json
import random
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from datetime import datetime
import os.path
from google.cloud import firestore
from google.oauth2.service_account import Credentials
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

## CONFIG

key_dict = json.loads(st.secrets["textkey"])
cred = credentials.Certificate(key_dict)

app = firebase_admin.initialize_app(cred)

db = firestore.client()

TUTOR_MODEL = random.choice([True, False])

# def logSession(session_history, filename):
#     f = open(filename, "a")
#     f.write("{0} -- {1}\n".format(datetime.now().strftime("%Y-%m-%d %H:%M"), session_history))
#     f.close()

# def checkStudentExists(filename):
#     if os.path.isfile(filename) is False:
#         return
#     with open(filename, 'r') as file_obj:
#         first_char = file_obj.read(1)
#         if not first_char:
#             return
#         else:
#             lines = file_obj.readlines()
#             if "'model': True" in lines[0]:
#                 st.session_state.model = True
#             elif "'model': False" in lines[0]:
#                 st.session_state.model = False


prompt_template = ChatPromptTemplate.from_messages([
    ("user", "{input}")
])

prompt_template_tutor=ChatPromptTemplate.from_messages([
    ("system", "Age como um tutor de programação proficiente em Inteligência Artificial."
            "Tens de assumir um tom {tone} em idioma {language}. Se o idioma for Português, usa Portugês de Portugal e não do Brasil. Assume também que o meu nível de conhecimento é {level}."
            "Para responder às minhas perguntas, deves ir buscar informação exclusivamente ao livro"
            " \"Stuart J. Russell, Peter Norvig - Artificial Intelligence: A Modern Approach 4th, Global Edition (2021, Pearson)."
            " Eu sou o(a) {name}, um(a) aluno(a) no segundo ano do curso Engenharia Informática, atualmente inscrito(a) numa disciplina sobre Inteligência Artificial."
            "A partir de agora, sempre que eu te fizer uma pergunta, responde à pergunta e certifica-te de que percebi a tua resposta, tentando ser o mais pedagógico possível."
            "Ser pedagógico é explicares 1. a matéria pedida com exemplos, 2. fazeres perguntas sobre a matéria para te certificares que entendi a tua explicação, 3. se eu errar essas"
            "perguntas, explicar novamente a matéria por outras palavras e voltar a fazer perguntas até teres a certeza que percebi."),
    MessagesPlaceholder(variable_name="chat_history"),
    ("user", "{input}")
])

output_parser = StrOutputParser()

def load_llm():
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=.5, openai_api_key = st.secrets["OPENAI_API_KEY"], streaming=True, callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]))
    return llm

llm = load_llm()

if TUTOR_MODEL == True:
    chain = prompt_template_tutor | llm | output_parser
elif TUTOR_MODEL == False:
    chain = prompt_template | llm | output_parser


## APP TUTOR

st.set_page_config(page_title="App Tutor", page_icon=":robot:", layout="wide")
st.title("App Tutor")

if "model" not in st.session_state:
    st.session_state.model = TUTOR_MODEL

## LOGIN
@st.experimental_dialog("Login")
def student():
    st.warning('**Não saltes este passo! É obrigatório para a tua experiência ficar registada!**', icon="⚠️")
    name = st.text_input("Name")
    id = st.text_input("IST-id")
    if st.button("Submit"):
        st.session_state.student.append({"Name": name, "IST-id": id})
        st.rerun()

if "student" not in st.session_state:
    st.session_state.student = []
    student()

col1, col2 = st.columns(2)

with col1: 
    
    if "answers" not in st.session_state:
        st.session_state.answers = []
    if "score" not in st.session_state:
        st.session_state.score = 0

    f = open('questions.json')
    questions = json.load(f)
    f.close()

    def list_answers():
        for i in range(0, len(questions)):
            id = st.session_state.answers[i]['question']
            if st.session_state.answers[i]['answer'] == st.session_state.answers[i]['selected']:
                st.write(f":green[{id}. Correto!]")
            else:
                st.write(f":red[{id}. Incorreto! A resposta é \"{st.session_state.answers[i]['answer']}\"]")


    @st.experimental_dialog("Submetido com Sucesso!")
    def submit(score):
        if score>=50:
            st.write(f":green[**Parabéns! A sua pontuação é {score}%.**]")
        else:
            st.write(f":red[**Ups! A sua pontuação é {score}%.**]")
        st.warning("Por favor, preenche o seguinte forms para deixar feedback sobre a experiência de utilização:\nhttps://forms.gle/EPENxtAkBfdAkJdu9")
        st.write("________________________")
        list_answers()

    def disable():
        st.session_state.disabled = True

    if "disabled" not in st.session_state:
        st.session_state.disabled = False

    ## QUIZ PERGUNTAS
    with st.container(height = 620):
        with st.form(key="evaluation", border=False):
            correct = 0
            incorrect = 10
            for i in range(0, len(questions)):
                st.write(questions[i]['id'], ".", questions[i]['questão'])
                if len(st.session_state.answers)<i+1:
                    st.session_state.answers.append({"question": questions[i]['id'], "answer": questions[i]['resposta'], "selected": None})
                option = st.radio("Escolhe uma das seguintes opções.", 
                                [questions[i]['A'], questions[i]['B'], questions[i]['C'], questions[i]['D']],
                                index = None, disabled=st.session_state.disabled)
                if option == questions[i]['A']:
                    if questions[i]['A'] == questions[i]['resposta']:
                        correct +=1
                        incorrect -= 1
                    if st.session_state.answers[i]['selected'] == None:
                        st.session_state.answers[i]['selected'] = option
                elif option == questions[i]['B']:
                    if questions[i]['B'] == questions[i]['resposta']:
                        correct +=1
                        incorrect -= 1
                    if st.session_state.answers[i]['selected'] == None:
                        st.session_state.answers[i]['selected'] = option
                elif option == questions[i]['C']:
                    if questions[i]['C'] == questions[i]['resposta']:
                        correct +=1
                        incorrect -= 1
                    if st.session_state.answers[i]['selected'] == None:
                        st.session_state.answers[i]['selected'] = option
                elif option == questions[i]['D']:
                    if questions[i]['D'] == questions[i]['resposta']:
                        correct +=1
                        incorrect -= 1
                    if st.session_state.answers[i]['selected'] == None:
                        st.session_state.answers[i]['selected'] = option
            

            submitted = st.form_submit_button(label="Submeter", on_click=disable, disabled=st.session_state.disabled)
            if submitted:
                score = correct/len(questions) * 100
                st.session_state.score = score
                submit(score)

with col2:

    if "setup" not in st.session_state:
        st.session_state.setup = []

    col1, col2, col3 = st.columns(3)
    with col1:
        tone=st.selectbox(
            'Tom',
            ('Formal','Informal')
        )

    with col2:
        language=st.selectbox(
            'Idioma',
            ('Português', 'English')
        )

    with col3:
        level=st.selectbox(
            'Nível de Conhecimento',
            ('Sei muito', 'Ainda sei pouco', 'Não sei nada')
        )

    st.session_state.setup.append({"tone": tone, "language": language, "level": level})
    
    for s in st.session_state.student:
        name = s["Name"]
        id = s["IST-id"]

    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({"role":"assistant", "content": f"Olá! O teu objetivo é concluíres o quizz do lado esquerdo do ecrã. Se tiveres alguma dúvida, estou aqui para te ajudar."})

    if "history" not in st.session_state:
        st.session_state.history = []
    
    ## CHAT
    with st.container(height=535):
        history = st.container(height=447)

        with history:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        if prompt := st.chat_input("Em que posso ajudar?"):
            with history:
                st.chat_message("user").markdown(prompt)
            st.session_state.messages.append({"role":"user", "content":prompt})
            st.session_state.history.append(HumanMessage(content=prompt))
            
            if TUTOR_MODEL == True:
                response = chain.stream({'tone': tone, 'language': language, 'level': level, 'name': name, 'input': prompt, 'chat_history': st.session_state.history})
            elif TUTOR_MODEL == False:
                response = chain.stream({'input':prompt})
            with history:
                with st.chat_message("ai"):
                    ai_response = st.write_stream(response)
            st.session_state.messages.append({"role":"assistant", "content":ai_response})
            st.session_state.history.append(AIMessage(content=ai_response))
            st.rerun()

if st.session_state.student != []:
    # doc_ref = db.collection("logs").document("logTeste")
    # doc = doc_ref.get()
    # if doc.exists:
    #     log = doc.todict()
    #     if doc.id == f"logTutor{id}":
    #         model = log['model']
    #         if model == True:
    #             TUTOR_MODEL = True
    #         elif model == False:
    #             TUTOR_MODEL = False

    doc_ref = db.collection("logs").document(f"logTutor{id}")
    doc_ref.set({"model": st.session_state.model,
                 "student": "teste",
                 "answers": "teste",
                 "score": "30",
                 "disabled": False,
                 "setup": "teste",
                 "messages": "teste",
                 "history": "teste"})

    # doc_ref.set({"date": datetime.datetime.now(),
    #             "model": True,
    #             "student": "teste",
    #             "answers": "teste",
    #             "score": "15",
    #             "disabled": False,
    #             "setup": "teste",
    #             "messages": "teste",
    #             "history": "teste"
    #             })

    # checkStudentExists(f"logs/logTutor{id}")
    # logSession(st.session_state, f"logs/logTutor{id}")

