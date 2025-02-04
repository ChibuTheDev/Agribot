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

# Suppress httpx logging
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM")
TIMEOUT = 50

# Function to check if the query is weather-related
def is_weather_query(message):
    """
    Check if the user is asking for weather information.
    """
    weather_keywords = ["weather", "forecast", "temperature", "rain", "sun", "cloud", "humidity"]
    return any(keyword in message.lower() for keyword in weather_keywords)


def extract_location(message):
    """
    Extract the location from the user's query.
    """
   
    location_indicators = ["in", "for", "at", "near", "around"]
    
    
    words = message.lower().split()
    
    # Find the location indicator and extract the location
    for i, word in enumerate(words):
        if word in location_indicators and i + 1 < len(words):
            return " ".join(words[i + 1:]).strip()
    
    #  assume the last word is the location if we dont see any indicator
    return words[-1].strip() if words else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        """Hi there, my name is Agribot and I dey for you. Ask me anything about Crop Recommendations and Management, Pest and Disease Control, Soil Health Tips, Livestock Management, and Sustainable Farming Practices. If you have any other questions or need help in other areas, feel free to ask. ps: I can also give you a 5-day weather forecast if you ask nicely 😉""",
        parse_mode=None
    )

async def handle_message_with_timeout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        user_message = update.message.text
        chat_id = update.message.chat_id

        
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")

        if chat_id not in context.chat_data:
            context.chat_data[chat_id] = {"history": []}

        history = context.chat_data[chat_id]["history"]

        
        if is_weather_query(user_message):
            try:
                
                location = extract_location(user_message)
                if not location:
                    await update.message.reply_text("Please specify a location.")
                    return

                # Get weather forecast
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
        else:
            # Handling non-weather queries
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
        # Created the app
        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Added handlers
        app.add_handler(CommandHandler("start", start))
        
        # Added message handler for all text messages
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message_with_timeout))
        
        # Added error handler
        app.add_error_handler(error_handler)
        
        # Start the bot
        logger.info("Starting Agribot...")
        app.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == '__main__':
    main()