import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

import siiau

import os

siiau.GetDataBase()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Soy un bot, porfavor hablame!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="eso lo puedo decir al revés: "+update.message.text[::-1])

async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="No entendí tu comando.")


async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    clases = list(map( str, siiau.Clase.find( context.args) ))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=clases)

async def coinciden(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sol = siiau.Clase.solapan( siiau.Clase.find( context.args) )
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sí" if sol else "No")

async def grafo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fname = siiau.Graficar( siiau.Clase.find( context.args) )
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=fname, filename="Grafo")
    os.remove(fname)


if __name__ == '__main__':
    application = ApplicationBuilder().token('6341907180:AAE-QpIUcFLvy_0RXEdwuH0hxzttoCofCPU').build()
    
    start_handler = CommandHandler('start', start)
    echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), echo)
    caps_handler = CommandHandler('caps', caps)
    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    info_handler = CommandHandler('info', info)
    coinciden_handler = CommandHandler('coinciden', coinciden)
    grafo_handler = CommandHandler('grafo', grafo)

    application.add_handler(start_handler)
    application.add_handler(caps_handler)
    application.add_handler(info_handler)
    application.add_handler(coinciden_handler)
    application.add_handler(grafo_handler)
    application.add_handler(echo_handler)
    application.add_handler(unknown_handler)
    
    application.run_polling()
