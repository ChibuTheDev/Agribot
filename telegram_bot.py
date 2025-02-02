import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TimedOut
from chat import get_chat_response
from weather_utils import get_5day_forecast
import logging

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM")
TIMEOUT = 50 

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        """Hi there, my name is Agribot and I dey for you. Ask me anything about Crop Recommendations and Management,  Pest and Disease Control,  Soil Health Tips Livestock Management and Sustainable Farming Practices. If you have any other questions or need help in other areas feel free to ask. ps: I can also give you a 5-day weather forecast if you ask nicely 😉""",
        parse_mode=None
    )

async def handle_message_with_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_message = update.message.text
        chat_id = update.message.chat_id

        # to show typing
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        if chat_id not in context.chat_data:
            context.chat_data[chat_id] = {"history": []}

        history = context.chat_data[chat_id]["history"]

        # Used asyncio.wait_for to implement timeout
        try:
            response, updated_history = await asyncio.wait_for(
                asyncio.create_task(get_chat_response_async(user_message, history)),
                timeout=TIMEOUT
            )
            context.chat_data[chat_id]["history"] = updated_history
            await update.message.reply_text(response, parse_mode=None)
            
        except asyncio.TimeoutError:
            logger.error(f"Response timed out for message: {user_message}")
            await update.message.reply_text(
                "I apologize, but the response is taking longer than expected. "
                "Please try asking your question again or break it into smaller parts.",
                parse_mode=None
            )

    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text(
            "I encountered an error processing your request. Please try again.",
            parse_mode=None
        )

async def get_chat_response_async(message, history):
    """Wrapper to make get_chat_response async"""
    return get_chat_response(message, history)

async def weather_forecast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_message = update.message.text
        chat_id = update.message.chat_id
        
        # Send typing action
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        if chat_id not in context.chat_data:
            context.chat_data[chat_id] = {"history": []}
        
        try:
            location = (user_message.lower().split("in")[-1].strip() 
                       if "in" in user_message.lower() 
                       else user_message.lower()
                       .replace("5 day forecast", "")
                       .replace("5-day forecast", "")
                       .replace("5 day weather", "")
                       .replace("breakdown the weather", "")
                       .strip())
            
            forecasts = await asyncio.wait_for(
                asyncio.create_task(get_weather_async(location)),
                timeout=TIMEOUT
            )
            
            await update.message.reply_text(forecasts, parse_mode=None)
            context.chat_data[chat_id]["history"].append({"role": "user", "parts": user_message})
            context.chat_data[chat_id]["history"].append({"role": "assistant", "parts": forecasts})
            
        except asyncio.TimeoutError:
            logger.error(f"Weather forecast timed out for location: {location}")
            await update.message.reply_text(
                "The weather forecast request is taking too long. Please try again.",
                parse_mode=None
            )
            
    except Exception as e:
        logger.error(f"Error in weather_forecast: {str(e)}")
        await update.message.reply_text(
            "I encountered an error getting the weather forecast. Please try again.",
            parse_mode=None
        )

async def get_weather_async(location):
    """Wrapper to make get_5day_forecast async"""
    return get_5day_forecast(location)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors"""
    try:
        if isinstance(context.error, TimedOut):
            if update and update.message:
                await update.message.reply_text(
                    "The request timed out. Please try again.",
                    parse_mode=None
                )
        else:
            logger.error(f"Update {update} caused error {context.error}")
            if update and update.message:
                await update.message.reply_text(
                    "An error occurred. Please try again later.",
                    parse_mode=None
                )
    except Exception as e:
        logger.error(f"Error in error_handler: {str(e)}")

def main():
    try:
        # Create and configure the application
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        
        # Add message handlers
        weather_filter = filters.Regex(r"(5 day forecast in|5-day forecast|5 day weather|breakdown the weather)")
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & weather_filter, weather_forecast))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_with_timeout))
        
        # Add error handler
        app.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("Starting Agribot...")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == '__main__':
    main()