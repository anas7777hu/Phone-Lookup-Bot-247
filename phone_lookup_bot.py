import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import phonenumbers
from phonenumbers import geocoder, carrier, timezone
from datetime import datetime

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Configuration
# NOTE: Using the provided token as a default if the environment variable is not set.
# For secure 24/7 deployment, set this token as a secret environment variable on the hosting service (e.g., Render/Railway).
BOT_TOKEN = os.getenv('BOT_TOKEN', '8264207818:AAFksNtrsNSOfG1GCtDkpsuhGgZ463qX_Lg')
ADMIN_ID = 8441069760

# Check if token is available
if not BOT_TOKEN:
    logger.error("BOT_TOKEN environment variable not set, and default token is missing. The bot cannot start.")
    # This check is more for local development, deployed services should handle this gracefully.

class PhoneNumberBot:
    def __init__(self, token):
        if not token:
            raise ValueError("Telegram Bot Token is required.")
            
        self.token = token
        try:
            self.app = Application.builder().token(token).build()
            logger.info("Bot application builder successful")
        except Exception as e:
            logger.error(f"Failed to build Application: {e}")
            raise
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")
        
        welcome_message = (
            f"👋 Welcome {user.first_name}!\n\n"
            "🔍 *फ़ोन नंबर ख़ुफ़िया जानकारी (Phone Number Lookup Bot)*\n\n"
            "यह बॉट आपको फ़ोन नंबरों की जाँच करने और सार्वजनिक रूप से उपलब्ध जानकारी एकत्र करने में मदद करता है।\n\n"
            "*उपलब्ध कमांड:*\n"
            "• /start - यह स्वागत संदेश दिखाएँ\n"
            "• /help - विस्तृत सहायता प्राप्त करें\n"
            "• /lookup - एक फ़ोन नंबर की जाँच करें\n"
            "• /about - इस बॉट के बारे में\n\n"
            "*जल्दी शुरू करें:*\n"
            "बस देश कोड के साथ एक फ़ोन नंबर भेजें!\n"
            "उदाहरण: +911234567890 या +14155552671\n\n"
            "⚠️ *अस्वीकरण:* यह उपकरण केवल शैक्षिक और खोजी उद्देश्यों के लिए है।"
        )
        
        try:
            await update.message.reply_text(welcome_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text("Welcome! Send me a phone number to get started.")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        help_text = (
            "📖 *विस्तृत सहायता गाइड*\n\n"
            "*कैसे उपयोग करें:*\n"
            "देश कोड (प्लस '+' सहित) के साथ एक फ़ोन नंबर भेजें\n\n"
            "*समर्थित फॉर्मेट:*\n"
            "• +[देश कोड][नंबर]\n"
            "• उदाहरण: +911234567890\n"
            "• उदाहरण: +14155552671\n\n"
            "*उपलब्ध सुविधाएँ:*\n"
            "✅ देश की पहचान\n"
            "✅ कैरियर/ऑपरेटर का पता लगाना\n"
            "✅ समय क्षेत्र (Timezone) की जानकारी\n"
            "✅ नंबर सत्यापन (Validation)\n"
            "✅ फॉर्मेट भिन्नताएँ\n"
            "✅ सर्च इंजन लिंक\n\n"
            "*जाँच विकल्प:*\n"
            "• Basic Info - त्वरित अवलोकन\n"
            "• All Features - सम्पूर्ण विश्लेषण\n"
            "• Search Links - सोशल मीडिया पर खोजें\n\n"
            "*टिप्स:*\n"
            "• हमेशा देश कोड शामिल करें\n"
            "• '+' प्रतीक से शुरू करें\n"
            "• स्पेस और विशेष वर्ण हटाएँ\n\n"
            "समर्थन चाहिए? व्यवस्थापक से संपर्क करें।"
        )
        
        try:
            await update.message.reply_text(help_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text("Help: Send a phone number with country code to get information.")
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """About command handler"""
        about_text = (
            "ℹ️ *फ़ोन नंबर ख़ुफ़िया बॉट के बारे में*\n\n"
            "वर्ज़न: 1.0.0\n"
            "स्टेटस: ✅ ऑनलाइन 24/7\n\n"
            "*उद्देश्य:*\n"
            "यह बॉट सार्वजनिक रूप से उपलब्ध डेटा स्रोतों का उपयोग करके फ़ोन नंबर जाँच क्षमताएँ प्रदान करता है।\n\n"
            "*प्रौद्योगिकी:*\n"
            "Python और python-telegram-bot लाइब्रेरी से निर्मित, सटीक डेटा प्रोसेसिंग के लिए phonenumbers लाइब्रेरी का उपयोग करता है।\n\n"
            "*सीमाएँ:*\n"
            "यह उपकरण ट्रैकिंग, हैकिंग या वास्तविक समय स्थान सेवाएँ प्रदान नहीं करता है। यह केवल सार्वजनिक रूप से उपलब्ध जानकारी प्राप्त करता है।\n\n"
            "⚡ बॉट 24/7 उपलब्धता के लिए क्लाउड इंफ्रास्ट्रक्चर पर होस्ट किया गया है।"
        )
        
        try:
            await update.message.reply_text(about_text, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error in about command: {e}")
            await update.message.reply_text("About: This is a phone number lookup bot running 24/7.")
    
    def validate_phone_number(self, phone_number):
        """Validate and parse phone number with improved error handling"""
        try:
            cleaned = re.sub(r'[^\d+]', '', phone_number)
            
            if not cleaned.startswith('+'):
                return None, "Phone number must start with + and country code"
            
            if len(cleaned) < 8:
                return None, "Phone number is too short"
            
            parsed = phonenumbers.parse(cleaned, None)
            
            if phonenumbers.is_valid_number(parsed):
                return parsed, None
            else:
                if phonenumbers.is_possible_number(parsed):
                    return parsed, "Number is possible but may not be valid"
                return None, "Invalid phone number format"
                
        except phonenumbers.phonenumberutil.NumberParseException as e:
            return None, f"Parse error: Could not recognize number: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in validate_phone_number: {e}")
            return None, "Error processing phone number"
    
    def get_basic_info(self, parsed_number):
        """Get basic information with comprehensive error handling"""
        try:
            country = "अज्ञात"
            carrier_name = "अज्ञात"
            timezones = []
            
            try:
                country = geocoder.description_for_number(parsed_number, "en") or "अज्ञात"
            except Exception as e:
                logger.error(f"Error getting country: {e}")
            
            try:
                carrier_name = carrier.name_for_number(parsed_number, "en") or "अज्ञात"
            except Exception as e:
                logger.error(f"Error getting carrier: {e}")
            
            try:
                timezones = timezone.time_zones_for_number(parsed_number) or []
            except Exception as e:
                logger.error(f"Error getting timezone: {e}")
            
            info = {
                'country': country,
                'carrier': carrier_name,
                'timezone': timezones,
                'number_type': phonenumbers.number_type(parsed_number),
                'international_format': phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
                'national_format': phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL),
                'e164_format': phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164),
                'is_possible': phonenumbers.is_possible_number(parsed_number),
                'is_valid': phonenumbers.is_valid_number(parsed_number),
                'country_code': parsed_number.country_code,
                'national_number': parsed_number.national_number
            }
            return info
            
        except Exception as e:
            logger.error(f"Error in get_basic_info: {e}")
            return None
    
    def get_search_links(self, phone_number):
        """Generate search engine links"""
        try:
            number_no_plus = phone_number.replace('+', '') 
            encoded = phone_number.replace('+', '%2B').replace(' ', '+')
            
            links = {
                'Google': f"https://www.google.com/search?q={encoded}",
                'TrueCaller': f"https://www.truecaller.com/search/in/{number_no_plus}",
                'Facebook': f"https://www.facebook.com/search/top/?q={encoded}",
                'LinkedIn': f"https://www.linkedin.com/search/results/all/?keywords={encoded}",
                'Twitter (X)': f"https://twitter.com/search?q={encoded}",
                'Instagram (Tag)': f"https://www.instagram.com/explore/tags/{number_no_plus}"
            }
            return links
        except Exception as e:
            logger.error(f"Error generating search links: {e}")
            return {}
    
    def format_number_type(self, number_type):
        """Convert number type enum to readable string"""
        types = {
            0: "फिक्स्ड लाइन (Fixed Line)",
            1: "मोबाइल (Mobile)",
            2: "फिक्स्ड लाइन या मोबाइल (Fixed Line or Mobile)",
            3: "टोल फ्री (Toll Free)",
            4: "प्रीमियम रेट (Premium Rate)",
            5: "साझा लागत (Shared Cost)",
            6: "VoIP",
            7: "व्यक्तिगत नंबर (Personal Number)",
            8: "पेजर (Pager)",
            9: "UAN",
            10: "वॉयसमेल (Voicemail)",
            -1: "अज्ञात (Unknown)"
        }
        return types.get(number_type, "अज्ञात (Unknown)")
    
    async def handle_phone_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle phone number input with comprehensive error handling"""
        try:
            phone_number = update.message.text.strip()
            user = update.effective_user
            
            logger.info(f"User {user.id} requested lookup for: {phone_number}")
            
            processing_msg = await update.message.reply_text("🔍 फ़ोन नंबर का विश्लेषण हो रहा है... कृपया प्रतीक्षा करें।")
            
            parsed, error = self.validate_phone_number(phone_number)
            
            if error and not parsed:
                await processing_msg.edit_text(
                    f"❌ {error}\n\n"
                    "कृपया देश कोड के साथ एक मान्य फ़ोन नंबर भेजें।\n"
                    "फ़ॉर्मेट: +[country code][number]\n"
                    "उदाहरण: +911234567890"
                )
                return
            
            context.user_data['phone_number'] = phone_number
            context.user_data['parsed_number'] = parsed
            
            keyboard = [
                [InlineKeyboardButton("📋 बुनियादी जानकारी (Basic Info)", callback_data='basic')],
                [InlineKeyboardButton("🔍 संपूर्ण जानकारी (All Features)", callback_data='all')],
                [InlineKeyboardButton("🌐 सर्च लिंक (Search Links)", callback_data='links')],
                [InlineKeyboardButton("❌ रद्द करें (Cancel)", callback_data='cancel')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            status_text = "✅ फ़ोन नंबर सफलतापूर्वक मान्य किया गया!"
            if error:
                status_text = f"⚠️ {error}"
            
            await processing_msg.edit_text(
                f"{status_text}\n\n"
                f"📱 नंबर: `{phone_number}`\n\n"
                f"कृपया वह जानकारी चुनें जिसे आप प्राप्त करना चाहते हैं:",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in handle_phone_number: {e}")
            try:
                await update.message.reply_text(
                    "❌ आपके अनुरोध को संसाधित करते समय एक त्रुटि हुई। "
                    "कृपया एक मान्य फ़ोन नंबर के साथ पुनः प्रयास करें।"
                )
            except:
                pass
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks with error handling"""
        try:
            query = update.callback_query
            await query.answer()
            
            choice = query.data
            
            if choice == 'cancel':
                await query.edit_message_text("❌ ऑपरेशन रद्द किया गया।")
                return
            
            phone_number = context.user_data.get('phone_number')
            parsed_number = context.user_data.get('parsed_number')
            
            if not phone_number or not parsed_number:
                await query.edit_message_text(
                    "❌ सत्र समाप्त हो गया है। कृपया फ़ोन नंबर फिर से भेजें।"
                )
                return
            
            await query.edit_message_text("⏳ जानकारी जुटाई जा रही है... कृपया प्रतीक्षा करें।")
            
            if choice == 'basic':
                result = self.generate_basic_info_report(parsed_number, phone_number)
            elif choice == 'all':
                result = self.generate_full_report(parsed_number, phone_number)
            elif choice == 'links':
                result = self.generate_links_report(phone_number)
            else:
                result = "❌ अमान्य विकल्प चुना गया।"
            
            await query.edit_message_text(
                result, 
                parse_mode='Markdown', 
                disable_web_page_preview=True
            )
            
            logger.info(f"Successfully processed {choice} request for {phone_number}")
            
        except Exception as e:
            logger.error(f"Error in button_callback: {e}")
            try:
                await query.edit_message_text(
                    "❌ जानकारी प्राप्त करते समय एक त्रुटि हुई। कृपया पुनः प्रयास करें।"
                )
            except:
                pass
    
    def generate_basic_info_report(self, parsed_number, phone_number):
        """Generate basic information report"""
        try:
            info = self.get_basic_info(parsed_number)
            
            if not info:
                return "❌ इस नंबर के लिए जानकारी प्राप्त नहीं की जा सकी।"
            
            timezone_str = ', '.join(info['timezone']) if info['timezone'] else 'अज्ञात'
            
            report = (
                f"📊 *बुनियादी जानकारी रिपोर्ट (Basic Information Report)*\n\n"
                f"📱 *फ़ोन नंबर:* `{phone_number}`\n\n"
                f"🌍 *देश:* {info['country']}\n"
                f"📡 *कैरियर:* {info['carrier']}\n"
                f"🕐 *समय क्षेत्र:* {timezone_str}\n"
                f"📞 *प्रकार:* {self.format_number_type(info['number_type'])}\n"
                f"🔢 *देश कोड:* +{info['country_code']}\n\n"
                f"*फॉर्मेट भिन्नताएँ:*\n"
                f"• अंतर्राष्ट्रीय: `{info['international_format']}`\n"
                f"• राष्ट्रीय: `{info['national_format']}`\n"
                f"• E164: `{info['e164_format']}`\n\n"
                f"*सत्यापन:*\n"
                f"• मान्य: {'✅ हाँ' if info['is_valid'] else '❌ नहीं'}\n"
                f"• संभव: {'✅ हाँ' if info['is_possible'] else '❌ नहीं'}\n\n"
                f"⚠️ *अस्वीकरण:* जानकारी सार्वजनिक रूप से उपलब्ध डेटा पर आधारित है।\n"
                f"📅 रिपोर्ट जनरेट की गई: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating basic report: {e}")
            return "❌ रिपोर्ट जनरेट करने में त्रुटि। कृपया पुनः प्रयास करें।"
    
    def generate_full_report(self, parsed_number, phone_number):
        """Generate comprehensive report"""
        try:
            info = self.get_basic_info(parsed_number)
            
            if not info:
                return "❌ इस नंबर के लिए जानकारी प्राप्त नहीं की जा सकी।"
            
            timezone_str = ', '.join(info['timezone']) if info['timezone'] else 'अज्ञात'
            
            report = (
                f"📊 *व्यापक जांच रिपोर्ट (COMPREHENSIVE INVESTIGATION REPORT)*\n"
                f"{'='*40}\n\n"
                f"🎯 *लक्ष्य नंबर:* `{phone_number}`\n\n"
                f"*🔍 बुनियादी जानकारी*\n"
                f"├─ देश: {info['country']}\n"
                f"├─ देश कोड: +{info['country_code']}\n"
                f"├─ कैरियर/ऑपरेटर: {info['carrier']}\n"
                f"├─ समय क्षेत्र: {timezone_str}\n"
                f"└─ नंबर प्रकार: {self.format_number_type(info['number_type'])}\n\n"
                f"*📋 फॉर्मेट भिन्नताएँ*\n"
                f"├─ अंतर्राष्ट्रीय: `{info['international_format']}`\n"
                f"├─ राष्ट्रीय: `{info['national_format']}`\n"
                f"├─ E164: `{info['e164_format']}`\n"
                f"└─ राष्ट्रीय नंबर: {info['national_number']}\n\n"
                f"*✓ सत्यापन स्थिति*\n"
                f"├─ मान्य नंबर: {'✅ हाँ' if info['is_valid'] else '❌ नहीं'}\n"
                f"└─ संभव नंबर: {'✅ हाँ' if info['is_possible'] else '❌ नहीं'}\n\n"
            )
            
            links = self.get_search_links(phone_number)
            if links:
                report += "*🔗 सर्च लिंक*\n"
                for platform, link in links.items():
                    report += f"├─ [{platform}]({link})\n"
                report += "\n"
            
            report += (
                f"*⚠️ महत्वपूर्ण अस्वीकरण*\n"
                f"यह उपकरण केवल सार्वजनिक स्रोतों से जानकारी प्रदान करता है। "
                f"यह ट्रैकिंग, हैकिंग, या वास्तविक समय स्थान डेटा प्रदान नहीं करता है। "
                f"कृपया जिम्मेदारी और नैतिक रूप से उपयोग करें।\n\n"
                f"📅 रिपोर्ट जनरेट की गई: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"🤖 बॉट स्थिति: ऑनलाइन 24/7"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating full report: {e}")
            return "❌ व्यापक रिपोर्ट जनरेट करने में त्रुटि। कृपया पुनः प्रयास करें।"
    
    def generate_links_report(self, phone_number):
        """Generate search links report"""
        try:
            links = self.get_search_links(phone_number)
            
            if not links:
                return "❌ सर्च लिंक जनरेट नहीं किए जा सके।"
            
            report = (
                f"🔗 *{phone_number} के लिए सर्च लिंक*\n\n"
                f"इस नंबर को विभिन्न प्लेटफार्मों पर खोजने के लिए नीचे दिए गए किसी भी लिंक पर क्लिक करें:\n\n"
            )
            
            for platform, link in links.items():
                report += f"🔹 [{platform}]({link})\n"
            
            report += (
                f"\n💡 *उपयोग के टिप्स:*\n"
                f"• ये लिंक सार्वजनिक रूप से उपलब्ध जानकारी खोजते हैं\n"
                f"• परिणाम प्लेटफॉर्म के अनुसार भिन्न हो सकते हैं\n"
                f"• कुछ प्लेटफार्मों के लिए लॉगिन आवश्यक हो सकता है\n"
                f"• सभी प्लेटफार्मों पर डेटा उपलब्ध नहीं हो सकता है\n\n"
                f"⚠️ इन उपकरणों का जिम्मेदारी से उपयोग करें और गोपनीयता कानूनों का सम्मान करें।"
            )
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating links report: {e}")
            return "❌ सर्च लिंक जनरेट करने में त्रुटि। कृपया पुनः प्रयास करें।"
    
    async def lookup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Lookup command handler"""
        try:
            await update.message.reply_text(
