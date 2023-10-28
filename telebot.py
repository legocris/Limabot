import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

import siiau

import os

#Cargar las bases de datos desde SIIAU
Ciclo = {}
Calendarios = []
def ActualizarBases(primero = 2017, ultimo = 2024):
    for anio in range(primero, ultimo):
        for ciclo in ("10","20"): #Calendario A es 202010, calendario B es 202020, etc
            calendario = str(anio)+ciclo
            base = siiau.BaseDatos(calendario)
            if not base.Datos:
                break
            Calendarios.append( calendario )
            Ciclo[calendario] = base


#Sinceramente no recuerdo qué hacía esto
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


#Estos son los comandos que le puedes enviar al boot.Si agregas un comando, no solo tienes que agregarlo aquí, también tienes que agragar el handler más abajo
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Soy un bot, porfavor hablame!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="eso lo puedo decir al revés: "+update.message.text[::-1]+ "\nEscribe el comando /ayuda para recibir ayuda")

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()+str(context.match)+" xd"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="No entendí tu comando. Informate usando /ayuda")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clases = list(map( str, D.find( context.args) ))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=clases)

async def coinciden(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sol = siiau.Clase.solapan( D.find( context.args) )
    text ="Sí" if sol else "No"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def grafo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fname = siiau.Graficar( D.find( context.args) )
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=fname, filename="Grafo")
    os.remove(fname)

async def calendariosDisponibles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calendarios = list(map( str, Calendarios ))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=calendarios)

async def cambiarCalendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ( (context.args[0]) in Calendarios):
        CicloActual = context.args[0]
        D = Ciclo[ CicloActual ]
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Se cambió al calendario "+CicloActual)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="El calendario no es válido")

async def calendarioActual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=CicloActual)

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Aiudaaa soy el Limabot:\n" 
    text += "Mi proposito es facilitar agendar materias de LIMA. "
    text += "La idea es poder visualizar qué materias se cruzan. "
    text += "De momento solo tengo la función de /grafo para este proposito. " 
    text += "Si dos materias se conectan en el grafo es que se puedn llevar juntas. "
    text += "Los NRC debes apuntarlos uno por uno despues del comando, también puedes poner CLABEs. "
    text += "\n\nComandos disponibles:"
    text += "\n/info #nrc1 #nrc2 #clave1 ..."
    text += "\n/grafo #nrc1 #nrc2 #clave1 ..."
    text += "\n/coinciden #nrc1 #nrc2 #clave1 ..."
    text += "\n/calendarios -> Calendarios Disponibles"
    text += "\n/calendario -> Calendario actual"
    text += "\n/cambiar -> Cambia el calendario actual"
    text += "\n/comandos -> Muestra los comandos disponibles"
    text += "\n/ayuda -> Ayuda"
    text += "\n\nCreditos: Jorge la idea de los grafos. Cristobal el bot"
    text += "\nGithub: https://github.com/legocris/Limabot"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "\n\nComandos disponibles:"
    text += "\n/info #nrc1 #nrc2 #clave1 ..."
    text += "\n/grafo #nrc1 #nrc2 #clave1 ..."
    text += "\n/coinciden #nrc1 #nrc2 #clave1 ..."
    text += "\n/calendarios -> Calendarios Disponibles"
    text += "\n/calendario -> Calendario actual"
    text += "\n/cambiar -> Cambia el calendario actual"
    text += "\n/comandos -> Muestra los comandos disponibles"
    text += "\n/ayuda -> Ayuda"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)


#aquí inicia la rutina
if __name__ == '__main__':
    #El token del bot de telegram es secreto y se pone en un archivo llamado "token.txt" 
    #debes solicitarlo si quieres modificar directamente el bot, ó crear tu propio bot
    f = open('token.txt','r')
    token = f.read()
    f.close()

    ActualizarBases()
    print("actualizados")
    CicloActual = Calendarios[-1]
    D = Ciclo[ CicloActual ]


    application = ApplicationBuilder().token(token).build()
    
    start_handler = CommandHandler('start', start)
    ayuda_handler = CommandHandler('ayuda', ayuda)
    comandos_handler = CommandHandler('comandos', comandos)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler('caps', caps)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    info_handler = CommandHandler('info', info)
    coinciden_handler = CommandHandler('coinciden', coinciden)
    grafo_handler = CommandHandler('grafo', grafo)
    calendarios_disponibles_handler = CommandHandler('calendarios', calendariosDisponibles)
    calendario_actual_handler = CommandHandler('calendario', calendarioActual)
    cambiar_calendario_handler = CommandHandler('cambiar', cambiarCalendario)
    

    application.add_handler(start_handler)
    application.add_handler(ayuda_handler)
    application.add_handler(comandos_handler)
    application.add_handler(caps_handler)
    application.add_handler(info_handler)
    application.add_handler(cambiar_calendario_handler)
    application.add_handler(calendarios_disponibles_handler)
    application.add_handler(calendario_actual_handler)
    application.add_handler(coinciden_handler)
    application.add_handler(grafo_handler)
    application.add_handler(echo_handler)
    application.add_handler(unknown_handler)
    
    application.run_polling()