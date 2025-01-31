import requests

from json import dumps

url = "http://localhost:8000/posts"

# Fazer uma requisição GET
def getInfo():
    response = requests.get(url)
    return response.json()

# Pega o ID máximo da db
def getMaxID():
    return max((post.get("id", 0) for post in getInfo()), default=0)

# Fazer uma requisição POST
def createUser(name, pw):
    new_post = {"id": getMaxID()+1, "username": name, "password": pw,
                "period": 1,  "calendar": [0], "listWs": []}
    response = requests.post(url, json=new_post)
    return new_post['id']

# Fazer uma requisição PUT
def editUser(user_id, mode="addTreino", novoTreino={"day":"", "name":"", "exercises":[]}):
    user = [post for post in getInfo() if post['id']==user_id][0] # Recupera o usuário que deve ser alterado na API a partir do selectedUser
    if mode=="attPeriod":
        # Atualiza diariamente o atributo período dos usuários.
        # Enquanto for menor que 30, apenas adicionará a lista, a partir disso, começará a limpar dias anteriores a 1 mês
        user["period"] += 1
        if user["period"] <= 30:
            user["calendar"].append(0)
        else:
            user["calendar"] = user["calendar"][1:].extend(0)
    elif mode=="attCalendar":
        user["calendar"][-1] = 1 # Marca o último dia como feito o treino
    elif mode=="addTreino":
        user["listWs"].append(novoTreino)
    elif mode[:-1]=="treino_":
        user["listWs"][int(mode[-1])-1] = novoTreino
    elif mode[:-1]=="delTreino_":
        del user["listWs"][int(mode[-1])-1]
    response = requests.put(f"{url}/{user_id}", json=user, headers={"Content-Type": "application/json"})

# Fazer uma requisição DELETE
def deleteUser(delete_name, delete_password):
    try:
        delete_user = [post for post in getInfo() if post['username']==delete_name][0]
        if delete_password == delete_user['password']:
            delete_url = f'{url}/{delete_user['id']}'
            response = requests.delete(delete_url)
            return response.status_code
        else:
            return 201
    except:
        return 201


# print(response.status_code)
