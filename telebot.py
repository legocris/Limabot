import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

import siiau

import os

#Cargar las bases de datos desde SIIAU
Ciclo = {}
Calendarios = []

def ActualizarBases(primero = 2017, ultimo = 2025):
    global Ciclo, Calendarios
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

def dict_a_texto(diccionario):
    texto = ""
    for nombre, propiedad in diccionario.items():
        texto += (f"{nombre}: {propiedad}\n")  # Use f-strings for clear formatting
    return texto

#Estos son los comandos que le puedes enviar al bot.Si agregas un comando, no solo tienes que agregarlo aquí, también tienes que agragar el handler más abajo
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
    clases = D.find( context.args)
    nombres = list(map( siiau.Clase.getNombre, clases ))
    NRCs = list(map( siiau.Clase.getNRC, clases ))
    claves = list(map( siiau.Clase.getClave, clases ))
    profesores = list(map( siiau.Clase.getProfesorCorto, clases ))
    
    diccionario = { claves[i]+'.'+NRCs[i] : nombres[i]+', '+profesores[i] for i in range(len(clases)) }
                       
    await context.bot.send_message(chat_id=update.effective_chat.id, text="```Lista\n"+dict_a_texto(diccionario)+"```", parse_mode="MarkdownV2")

async def raw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clases = list(map( str, D.find( context.args) ))
    await context.bot.send_message(chat_id=update.effective_chat.id, text="```Lista\n"+str(clases)+"```", parse_mode="MarkdownV2")


async def nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clases = D.find( context.args)
    nombres = list(map( siiau.Clase.getNombre, clases ))
    NRCs = list(map( siiau.Clase.getNRC, clases ))
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="```Lista\n"+dict_a_texto(dict( zip(NRCs, nombres) ))+"```", parse_mode="MarkdownV2")

async def horario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clases = D.find( context.args)
    horarios = list(map( siiau.Clase.getHorarios, clases ))
    NRCs = list(map( siiau.Clase.getNRC, clases ))
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="```Lista\n"+dict_a_texto(dict( zip(NRCs, horarios) ))+"```", parse_mode="MarkdownV2")

async def profesor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clases = D.find( context.args)
    profesores = list(map( siiau.Clase.getProfesor, clases ))
    NRCs = list(map( siiau.Clase.getNRC, clases ))
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text="```Lista\n"+dict_a_texto(dict( zip(NRCs, profesores) ))+"```", parse_mode="MarkdownV2")


async def malla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    diccionario = {}
    if context.args == []:
        claves = D.ClaveDict.keys()
        materias =  [ list(dict_nrc.values())[0] for dict_nrc in D.ClaveDict.values() ]
        nombres = list(map( siiau.Clase.getNombre, materias ))
        diccionario |= dict(zip(claves, nombres))
    else:
        for arg in context.args:
            claves = D.malla[arg]
            materias = [ list(dict_nrc.values())[0] for dict_nrc in [D.ClaveDict[clave] for clave in claves] ]
            nombres = list(map( siiau.Clase.getNombre, materias ))
            diccionario |= dict(zip(claves, nombres))

    await context.bot.send_message(chat_id=update.effective_chat.id, text="```Lista\n"+dict_a_texto( diccionario )+"```", parse_mode="MarkdownV2")

async def coinciden(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sol = siiau.Clase.solapan( D.find( context.args) )
    text ="Sí" if sol else "No"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def grafo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fname = siiau.Graficar( D.find( context.args) )
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=fname, filename="Grafo")
    os.remove(fname)

async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fname = siiau.GraficarCalendario( D.find( context.args) )
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=fname, filename="calendario")
    os.remove(fname)

async def calendariosDisponibles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calendarios = list(map( str, Calendarios ))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=calendarios)

async def cambiarCalendario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ( (context.args[0]) in Calendarios):
        global CicloActual, D
        CicloActual = context.args[0]

        D = Ciclo[ CicloActual ]
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Se cambió al calendario "+CicloActual)
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="El calendario no es válido")

async def calendarioActual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=CicloActual)

async def mallaImagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo='Archivos/mapa_curricular_lima_2023b.png', filename="Malla 2023b")

async def mallaPdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_document(chat_id=update.effective_chat.id, document='Archivos/mapa_curricular_lima_2023b.pdf', filename="mapa_curricular_lima_2023b")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Aiudaaa soy el Limabot:\n" 
    text += "Mi proposito es facilitar agendar materias de LIMA. "
    text += "La idea es poder visualizar qué materias se cruzan. "
    text += "Tengo la función /grafo y /calendario para este proposito. " 
    text += "Si dos materias se conectan en el grafo es que se puedn llevar juntas. "
    text += "Los NRC debes apuntarlos uno por uno despues del comando, también puedes poner CLAVES, ó comandos como"
    text += "\n\nComandos disponibles:"
    text += "\n/malla primero segundo ... noveno"
    text += "\n/info #nrc1 #nrc2 #clave1 primero-noveno ..."
    text += "\n/grafo #nrc1 #nrc2 #clave1 primero-noveno ..."
    text += "\n/calendario #nrc1 #nrc2 #clave1 primero-noveno..."
    text += "\n"
    text += "\n Otros comandos quizá menos importantes"
    text += "\n/malla_imagen"
    text += "\n/malla_pdf"
    text += "\n/coinciden #nrc1 #nrc2 #clave1 ..."
    text += "\n/nombre #nrc1 #nrc2 #clave1 ..."
    text += "\n/profesor #nrc1 #nrc2 #clave1 ..."
    text += "\n/horario #nrc1 #nrc2 #clave1 ..."
    text += "\n/comandos -> Muestra los comandos disponibles"
    text += "\n/ayuda -> Ayuda"
    text += "\n\nCreditos: Cristobal y Jorge por la idea de los grafos. "
    text += "\nGithub: https://github.com/legocris/Limabot"

    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def comandos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text  = "\n\nComandos disponibles:"
    text += "\n/malla primero segundo ... noveno"
    text += "\n/info #nrc1 #nrc2 #clave1 primero-noveno ..."
    text += "\n/grafo #nrc1 #nrc2 #clave1 primero-noveno ..."
    text += "\n/calendario #nrc1 #nrc2 #clave1 primero-noveno..."
    text += "\n"
    text += "\n Otros comandos quizá menos importantes"
    text += "\n/malla_imagen"
    text += "\n/malla_pdf"
    text += "\n/coinciden #nrc1 #nrc2 #clave1 ..."
    text += "\n/nombre #nrc1 #nrc2 #clave1 ..."
    text += "\n/profesor #nrc1 #nrc2 #clave1 ..."
    text += "\n/horario #nrc1 #nrc2 #clave1 ..."
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
    CicloActual = Calendarios[-2]
    D = Ciclo[ CicloActual ]


    application = ApplicationBuilder().token(token).build()
    
    start_handler = CommandHandler('start', start)
    ayuda_handler = CommandHandler('ayuda', ayuda)
    comandos_handler = CommandHandler('comandos', comandos)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler('caps', caps)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    raw_handler = CommandHandler('raw', raw)
    info_handler = CommandHandler('info', info)
    nombre_handler = CommandHandler('nombre', nombre)
    profesor_handler = CommandHandler('profesor', profesor)
    horario_handler = CommandHandler('horario', horario)
    malla_handler = CommandHandler('malla', malla)
    coinciden_handler = CommandHandler('coinciden', coinciden)
    grafo_handler = CommandHandler('grafo', grafo)
    calendario_handler = CommandHandler('calendario', calendario)
    calendarios_disponibles_handler = CommandHandler('calendarios_disponibles', calendariosDisponibles)
    calendario_actual_handler = CommandHandler('calendario_actual', calendarioActual)
    cambiar_calendario_handler = CommandHandler('cambiar_calendario', cambiarCalendario)
    mostrar_malla_imagen_handler = CommandHandler('malla_imagen', mallaImagen)
    mostrar_malla_pdf_handler = CommandHandler('malla_pdf', mallaPdf)
    

    application.add_handler(start_handler)
    application.add_handler(ayuda_handler)
    application.add_handler(comandos_handler)
    application.add_handler(caps_handler)
    application.add_handler(raw_handler)
    application.add_handler(info_handler)
    application.add_handler(nombre_handler)
    application.add_handler(profesor_handler)
    application.add_handler(horario_handler)
    application.add_handler(malla_handler)
    application.add_handler(mostrar_malla_imagen_handler)
    application.add_handler(mostrar_malla_pdf_handler)
    application.add_handler(cambiar_calendario_handler)
    application.add_handler(calendarios_disponibles_handler)
    application.add_handler(calendario_actual_handler)
    application.add_handler(coinciden_handler)
    application.add_handler(grafo_handler)
    application.add_handler(calendario_handler)
    application.add_handler(echo_handler)
    application.add_handler(unknown_handler)
    
    application.run_polling()