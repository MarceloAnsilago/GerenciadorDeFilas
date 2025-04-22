from fastapi import FastAPI
from pydantic import BaseModel
from supabase import create_client
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()  # Carrega o .env
app = FastAPI()

# Configure CORS (para chamadas do frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
# Modelo para endpoints que precisam apenas de uma seção
class SecaoInput(BaseModel):
    secao: int

# Modelo para inserção de nova senha
class SenhaInput(BaseModel):
    secao: int
    senha: int
    hora: str
    usuario: str
    resposta: str
    status: str
    terminal: int
    unidade: str
    prioridade: str = "normal"  # Novo campo com valor padrão
    
@app.post("/init-secao")
def init_secao(dados: SecaoInput):
    """
    Verifica se a seção já existe; se não, insere um registro inicial.
    """
    data = supabase.table("senha").select("*").eq("secao", dados.secao).execute()
    if data.data and len(data.data) > 0:
        return {"mensagem": f"Seção {dados.secao} já existe."}
    else:
        initial_data = {
            "secao": dados.secao,
            "senha": 0,
            "hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "usuario": "admin",
            "resposta": "chamando 1",
            "status": "encerrado",
            "terminal": 0,
            "unidade": "São Miguel Idaron"
        }
        response = supabase.table("senha").insert(initial_data).execute()
        if response.data:
            return {"Olá": f"Seção {dados.secao} criada com sucesso!"}
        else:
            return {"erro": "Falha ao criar a seção."}

@app.get("/tem-senha-aberta")
def tem_senha_aberta(secao: int):
    """
    Verifica se existe alguma senha com status 'aberto' para a seção.
    """
    data = supabase.table("senha")\
        .select("*")\
        .eq("secao", secao)\
        .eq("status", "aberto")\
        .limit(1)\
        .execute()
    return {"aberta": bool(data.data)}

@app.get("/senha-atual")
def get_senha_atual(secao: int):
    """
    Retorna a senha atual com status 'aberto', ou a última encerrada se não houver aberta.
    """
    # Tenta buscar a última senha com status "aberto"
    aberta = supabase.table("senha")\
        .select("*")\
        .eq("secao", secao)\
        .eq("status", "aberto")\
        .order("hora", desc=True)\
        .limit(1)\
        .execute()
    
    if aberta.data:
        return aberta.data[0]
    
    # Se não houver nenhuma aberta, retorna a última encerrada
    encerrada = supabase.table("senha")\
        .select("*")\
        .eq("secao", secao)\
        .eq("status", "encerrado")\
        .order("hora", desc=True)\
        .limit(1)\
        .execute()
    
    if encerrada.data:
        return encerrada.data[0]

    # Caso não exista nenhuma senha ainda
    return {}
@app.get("/ultimas-senhas")
def get_ultimas_senhas(secao: int):
    """
    Retorna as 8 últimas senhas ENCERRADAS em ordem decrescente de chamada (por ID).
    """
    data = supabase.table("senha")\
        .select("*")\
        .eq("secao", secao)\
        .eq("status", "encerrado")\
        .order("id", desc=True)\
        .limit(8)\
        .execute()
    return data.data

@app.post("/gravar-senha")
def gravar_senha(dados: SenhaInput):
    """
    Insere uma nova senha na tabela.
    """
    response = supabase.table("senha").insert(dados.dict()).execute()
    if response.data:
        return {"mensagem": "Senha gravada com sucesso!"}
    else:
        return {"erro": "Falha ao gravar senha"}
    
@app.get("/todas-senhas")
def get_todas_senhas(secao: int):
    """
    Retorna TODAS as senhas da seção (ordenadas pelo número da senha).
    """
    data = supabase.table("senha").select("*").eq("secao", secao).order("senha", desc=False).execute()
    return data.data    

@app.put("/atualizar-senha/{id}")
def atualizar_senha(id: int, dados: dict):
    return supabase.table("senha").update(dados).eq("id", id).execute()



@app.get("/validar-secao")
def validar_secao(secao: int):
    """
    Verifica se existem senhas na seção informada.
    """
    data = supabase.table("senha").select("*").eq("secao", secao).limit(1).execute()
    return {"existe": bool(data.data)}



# #cd "D:\Documentos\Gerenciador de Senhas Streamlit3\ProjetoSenhas\backend-api"
# # uvicorn main:app --reload
# # http://127.0.0.1:8000/senha-atual?secao=1049