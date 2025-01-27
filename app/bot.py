from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler

from request import getInfo, createUser, deleteUser, editUser

# Define globalmente o scheduler, pra rodar de forma independente
scheduler = BackgroundScheduler()

#Simplificador para enviar mensagens
createSendFunc = lambda update: (lambda string, keyboard=[]: update.message.reply_text(string, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)))

getActualUser = lambda context: [x for x in getInfo() if x['id']==context.user_data.get("selectedUser")][0]

def updateUsersPeriod():
    for user in getInfo():
        editUser(user['id'], mode="attPeriod")

def updateUserCalendar(user_id):
    editUser(user_id, mode="attCalendar")

# Função para responder ao comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Olá. Estou aqui para te ajudar a controlar e visualizar seus treinos.\nUse /help para ver meus comandos.')
    await update.message.reply_text('Utilize /newuser para criar um novo usuário, ou logue utilizando /login.')

# Função para responder ao comando /newuser
async def addUser(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Boas vindas, novo usuário. Digite seu nome e sua senha:\n_Exemplo:\nusuario123\nminha-senha_', parse_mode="Markdown")
    #  Cria um estado para esperar o nome, fazendo com que só seja captado o username na próxima mensagem.
    context.user_data["awaiting_name"] = True

# Função para registrar os textos, que não são comandos.
async def handleMsg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    send = createSendFunc(update)
    async def pegarInfoTreino():
        data = update.message.text.split("\n")
        if len(data)<3: return "error"
        return {"day": data[1], "name": data[0], "exercises": data[2:]}

    # Quando o esperado for o nome do novo usuário
    if context.user_data.get("awaiting_name"):
        userData = update.message.text.split("\n")
        try:
            newUser = userData[0]
            password = userData[1]
            context.user_data["selectedUser"] = createUser(newUser, password) # Cria o usuário e faz um post na db. Retorna o index do novo usuário
            await send(f'Muito prazer, *{newUser}*. Foi criado um banco para armazenar as informações sobre seus próximos treinos.')
            context.user_data["awaiting_name"] = False
            await send(f"O usuário atual agora é *{newUser}*.")
        except:
            await send(f'Operação cancelada (informações insuficientes)')
            context.user_data["awaiting_name"] = False

    # Quando o esperado forem os dados do login
    if context.user_data.get("awaiting_login"):
        userData = update.message.text.split("\n")
        try:
            nameUser = userData[0]
            password = userData[1]
            try:
                actUserData = list(filter(lambda x: x['username']==nameUser, getInfo()))[0] #Post do usuário encontrado
                if actUserData["password"] == password:
                    context.user_data["selectedUser"] = actUserData['id'] # Cria o usuário e faz um post na db. Retorna o index do novo usuário
                    await send(f"O usuário atual agora é *{nameUser}*. Bem vindo de volta.")
                else: # Senha errada
                    await send(f"Senha incorreta.")
            except: #usuário inexistente
                await send("Usuário inexistente.")
        except: # Usuário forneceu poucas informações
            await send(f'Operação cancelada (informações insuficientes)')
    
        context.user_data["awaiting_login"] = False

    # Quando o esperado for o nome do usuário a ser deletado
    elif context.user_data.get("awaiting_del"):
        userData = update.message.text.split("\n")
        try:
            delUser = userData[0]
            delPassword = userData[1]
            status = deleteUser(delUser, delPassword)
            if status==200:
                await send(f'O usuário *{delUser}* foi deletado com sucesso.')
            else:
                await send("Usuário inexistente ou senha incorreta.")
        except:
            await send(f'Operação cancelada (informações insuficientes)')

    # Quando o esperado forem as informações do treino adicionado/editado
    elif context.user_data.get("awaiting_addTrainingInfo"):
        infoTreino = await pegarInfoTreino()
        if infoTreino=="error":
            await send("Operação cancelada (informações insuficientes).")
        else:
            editUser(context.user_data.get("selectedUser"), novoTreino=infoTreino)
            await send(f"Seu treino foi adicionado.")
        context.user_data["awaiting_addTrainingInfo"] = False

    elif context.user_data.get("awaiting_editTrainingInfo"):
        infoTreino = await pegarInfoTreino()
        if infoTreino=="error":
            await send("Operação cancelada (informações insuficientes).")
        else:
            editUser(context.user_data.get("selectedUser"), mode=context.user_data["awaiting_editTrainingInfo"], novoTreino=infoTreino)
            await send(f"O *treino {context.user_data["awaiting_editTrainingInfo"][-1]}* foi alterado.")
        context.user_data["awaiting_editTrainingInfo"] = False

# Função para manipular as ações dos botões
async def handleButton(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    action = query.data # Pega o valor do callback data do botão apertado

    if action == "addTreino" or action[:-1] == "treino_":
        # await query.message.reply_text("Digite:\n- O nome do treino:\n- Que dia será feito:\n- Os exercícios, no formato:\n_(4x12) Supino reto\n(3x10) Barra fixa [...]_", parse_mode="Markdown")
        await query.message.reply_text("Digite, por exemplo:\n- Treino de braço:\n- Quarta-feira:\n_(4x12) Rosca Scott\n(3x10) Tríceps na polia alta [...]_", parse_mode="Markdown")        
        if action == "addTreino":
            context.user_data["awaiting_addTrainingInfo"] = True
        else:
            context.user_data["awaiting_editTrainingInfo"] = action
    elif action[:-1] == "delTreino_":
        editUser(context.user_data.get("selectedUser"), mode=action)
        await query.message.reply_text(f"O *treino {action[-1]}* foi excluído.", parse_mode="Markdown")


async def showUserInfo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Informações:\n{str(getInfo())}')

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Para deletar uma conta, digite o nome do usuário e a senha:\n_Exemplo:\nusuario123\nminha-senha_', parse_mode="Markdown")
    context.user_data["awaiting_del"] = True

async def openTreinos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    send = createSendFunc(update) # Cria send como uma função no escopo de openConfig, uma vez que depende do objeto para funcionar.

    actUserData = {}

    try:
        actUserData = list(filter(lambda x: x['id']==context.user_data.get("selectedUser"), getInfo()))[0]
    except:
        await send("Você ainda não tem usuários salvos.")
        return

    # await update.message.reply_text(str(actUserData))
    await send("Suas configurações:")
    
    listaTreinos = actUserData['listWs']
    nTreinos = len(listaTreinos)
    # await update.message.reply_text(f"*Treinos semanais:* {nTreinos}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Adicionar Treino", callback_data=f"addTreino")]]))
    await send(f"*Treinos semanais:* {nTreinos}", [[InlineKeyboardButton("Adicionar Treino", callback_data=f"addTreino")]])


    for i in range(0, nTreinos):
        # Define o teclado de botões para cada treino (botão de editar)
        trainingKeyboard = [
            [
                InlineKeyboardButton(f"Editar", callback_data=f"treino_{i+1}"), InlineKeyboardButton("Deletar", callback_data=f"delTreino_{i+1}")
            ]
        ]
        await send(f"*{listaTreinos[i]['day'].upper()} - {listaTreinos[i]['name']}*\n"+
              "\n".join([f'- {ex}' for ex in listaTreinos[i]['exercises']]), trainingKeyboard)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    commandList = {
                    "treinos": "Permite ver e alterar seus treinos",
                    "delete": "Deleta um usuário",
                    "help": "Exibe um menu de ajuda",
                    "login": "Entra em uma conta existente",
                    "mark": "Registra o treino de hoje como feito",
                    "newuser": "Cria um novo usuário",
                    "start": "Te dá as boas vindas :)",
                    "status": "Mostra o seu rendimento",
                }
    await update.message.reply_text("Aqui está uma lista com todos os comandos que atendo:\n"+
    "\n".join([f'*/{command}*: {commandList[command]}' for command in commandList.keys()]), parse_mode='Markdown')

# async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE, mode="commands") -> None:
#     commandList = ["treinos", "delete", "help", "newuser", "start", "users"]
#     await update.message.reply_text("Aqui está uma lista com todos os comandos que atendo:\n",
#     reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(command, callback_data=f"/{command}")] for command in range(0, len(commandList))]))

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text('Para acessar uma conta, digite o nome do usuário e a senha:\n_Exemplo:\nusuario123\nminha-senha_', parse_mode="Markdown")
    context.user_data["awaiting_login"] = True

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from math import ceil, floor
    send = createSendFunc(update)
    actualUser = getActualUser(context)

    diasTotal, diasTreinados, metaSemanal = len(actualUser["calendar"]), actualUser["calendar"].count(1), len(actualUser["listWs"])
    diasEsperados = ceil(diasTotal/7) * metaSemanal - (metaSemanal-diasTotal%7) # Contando com correção para semanas incompletas.
    if diasEsperados <= 0: diasEsperados = 1

    await send(f"Seu rendimento atual é de:")
    percentage = ceil(100*(diasTreinados/diasEsperados))
    await send(f"{"|█"*floor(percentage*20/100)}{"|░"*ceil((100-percentage)*20/100)}| ({percentage}%)\n"+
               f"Meta de {metaSemanal} treinos na semana nos últimos {diasTotal} dias.\n"+
               f"_{diasTreinados}/{diasEsperados}_ treinos feitos nesse período.")

async def markAsComplete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    from random import choice
    try:
        updateUserCalendar(context.user_data.get("selectedUser"))
        await update.message.reply_text(choice(["A de hoje tá paga. Boa!", "Treino completo, continue assim.", "Feito, descanse para a próxima."]))
    except:
        await update.message.reply_text("Você não está em uma conta válida.")

# Função para forçar a pulada de dia (desativado)
# async def forceDay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     updateUsersPeriod()

# Função principal
def main():
    app = Application.builder().token("7679308466:AAHiMaWJfmHjGkgo-UuMfsH1ywDmjZjCQq8").build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handleMsg))
    app.add_handler(CallbackQueryHandler(handleButton))

    app.add_handler(CommandHandler("start", start))
    # app.add_handler(CommandHandler("show", showUserInfo))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("login", login))
    app.add_handler(CommandHandler("newuser", addUser))
    app.add_handler(CommandHandler("treinos", openTreinos))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("mark", markAsComplete))

    # Função que chamará a atualização do período dos usuários sempre à meia-noite
    scheduler.add_job(updateUsersPeriod, 'cron', hour=0, minute=0)
    scheduler.start()

    print("Bot Rodando.")
 
    # Inicia o bot
    app.run_polling()


import uvicorn
from watchgod import run_process

# Sempre que houver modificação em algum arquivo do diretório app, a função main será rodada novamente
if __name__ == "__main__":
    run_process("./", main)