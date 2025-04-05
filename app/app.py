from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pathlib import Path
from typing import List
import copy
import json

# Caminho para o arquivo JSON
DATA_FILE = Path("data.json")

# Inicializa o arquivo se ele não existir
if not DATA_FILE.exists():
    DATA_FILE.write_text(json.dumps([]))

# Função para carregar os dados
def load_data():
    with DATA_FILE.open("r") as file:
        return json.load(file) 

# Função para salvar os dados
def save_data(data):
    with DATA_FILE.open("w") as file:
        json.dump(data, file, indent=4)

# Modelo de dados
class User(BaseModel):
    id: int | None = None  # ID será gerado automaticamente
    username: str          # Nome do usuário
    password: str           
    period: int            # Há quanto tempo o usuário registra
    calendar: List         # Dias treinados com exito
    bodyInfos: List        # Lista de informações corporais
    listWs: List           # Lista contendo os treinos do usuário

# Inicializa o FastAPI
app = FastAPI()

@app.get("/posts/", response_model=list[User])
def get_posts():
    return load_data()


@app.get("/posts/{post_id}", response_model=User)
def get_post(post_id: int):
    data = load_data()
    for user in data:
        if user['id'] == post_id:
            return user
    raise HTTPException(status_code=404, detail="Post not found")


@app.post("/posts/", response_model=User)
def create_post(post: User):
    data = load_data()
    data.append(post.dict())
    save_data(data)
    return post

@app.put("/posts/{post_id}", response_model=User)
def edit_post(post_id: int, post: User):
    data = load_data() 
    for i, user in enumerate(data):
        if user['id']==post_id:
            copiedPost = copy.deepcopy(post.__dict__)
            data[i] = copiedPost
            break
    save_data(data)
    return post

@app.delete("/posts/{post_id}", response_model=dict)
def delete_post(post_id: int):
    data = load_data()
    filtered_data = [item for item in data if item["id"] != post_id]
    if len(filtered_data) == len(data):  # ID não encontrado
        raise HTTPException(status_code=404, detail="User not found")
    save_data(filtered_data)
    return {"message": f"User with ID {post_id} deleted"}

import uvicorn
def runFastApi():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    # run_process("./", run)
    runFastApi()
    
    
