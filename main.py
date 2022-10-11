from datetime import datetime, timedelta
from telegram import *
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import logging
import csv

updater = Updater(token='1503566543:AAG6r9DFIik4UA7xEFfVRCCx_305Xj64Lkg')
dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

admin_keyboard_pl = [
    [InlineKeyboardButton("Sprawdź oczekujących", callback_data="awaiting_approval")]]

sure_keyboard_pl = [
    [InlineKeyboardButton("Tak", callback_data="yes")],
    [InlineKeyboardButton("Nie", callback_data="no")]]

user_keyboard_pl = [
    [InlineKeyboardButton("Kup dostęp", callback_data="buy_vip")]]

go_await_keyboard_pl = [
    [InlineKeyboardButton("Potwierdź", callback_data="add_to_awaiting"),
     InlineKeyboardButton("Wróć", callback_data="back_to_menu")]]

add_await_keyboard_pl = [
    [InlineKeyboardButton("Dodaj", callback_data="add_to_users"),
     InlineKeyboardButton("Usuń z listy", callback_data="delete_from_awaiting")]]


def get_all_users(filename):
    """Returns current users from specified file, if there's none returns empty list.

    :param filename: Name of file to check users (for example: users.csv)."""
    all_records = []
    try:
        with open(filename, 'r') as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                user_id = int(row[0])
                user_nick = str(row[1])
                due_date = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S.%f')
                is_admin = eval(row[3])
                user = [user_id, user_nick, due_date, is_admin]
                all_records.append(user)
    except FileNotFoundError:
        with open(filename, 'w+') as file:
            csvwriter = csv.writer(file)
            csvwriter.writerow('')
        return all_records
    return all_records


def check_if_admin(user_id):
    """Returns True if user specified by provided id is admin.

    :param user_id: ID of user to check admin privileges."""
    users = get_all_users("users.csv")
    for user in users:
        if user[3] and user_id == user[0]:
            return True
        else:
            return False


def send_picture(update: Update, _: CallbackContext):
    """Sends photo to all users if admin send photo to chat."""
    # TODO should check if admin
    message = f'Zdjęcie wysłane!'
    users = get_all_users("users.csv")
    for user in users:
        if user[0] != update.message.from_user.id:
            _.bot.send_photo(user[0], update.message.photo[0].file_id)
    if message != update.message.text:
        update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(admin_keyboard_pl))


"""def send_to_many(update: Update, context: CallbackContext, text):
    users = get_all_users("users.csv")
    for user in users:
        context.bot.send_message(391644337, text)
        sleep(0.1)"""


def send_message(update: Update, _: CallbackContext):
    """Sends message to all users if admin sends message to chat."""
    check_if_admin(update.message.from_user.id)
    # TODO chyba nie sprawdza do końca czy admin xD
    message = f'Wiadomość wysłana!\n- -{update.message.text}- -'
    users = get_all_users("users.csv")
    for user in users:
        if user[0] != update.message.from_user.id:
            _.bot.send_message(user[0], update.message.text)
    if message != update.message.text:
        update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(admin_keyboard_pl))


def buy_vip(update):
    """Sent to user if Buy Vip button used."""
    message = "Opłać konto VIP, napisz do @TenTyp i potwierdź tutaj."
    if message != update.message.text:
        update.edit_message_text(message, reply_markup=InlineKeyboardMarkup(go_await_keyboard_pl))


def back_to_menu(update: Update):
    """Come back to main user menu if Return button used."""
    welcoming = update.message.chat.username
    message = f"Witaj, {welcoming}!"
    update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(user_keyboard_pl))


def add_to_awaiting(update):
    """Adds user to awaiting file after confirmation by such user."""
    filename = "awaiting.csv"
    user_id = update.message.chat.id
    username = update.message.chat.username
    data = [user_id, username]
    save_to_file(data, filename)
    message = f"Dodano do listy oczekujących"
    update.edit_message_text(message)


def awaiting_approval(update):
    """Adds user to users file (vip) after confirmation of payment by admin."""
    awaiting = get_all_users("awaiting.csv")
    if awaiting:
        awaiting_users = []
        for user in awaiting:
            awaiting_users.append(user)
            message = user[1]
            update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(add_await_keyboard_pl))
    else:
        message = "Nie ma oczekujących na dołączenie."
        if message != update.message.text:
            update.edit_message_text(message, reply_markup=InlineKeyboardMarkup(admin_keyboard_pl))


def start(update: Update, _: CallbackContext):
    """First contact with bot."""
    welcoming = update.message.from_user.username
    client = update.message.from_user
    if check_if_admin(update.message.from_user.id):
        update.message.reply_text(f'Witaj, {welcoming}!', reply_markup=InlineKeyboardMarkup(admin_keyboard_pl))
    else:
        update.message.reply_text(f'Witaj, {welcoming}!', reply_markup=InlineKeyboardMarkup(user_keyboard_pl))


def check_answer(query, update, context):
    """For checking which button was used and acting accordingly."""
    data = query.data
    if data == "awaiting_approval":
        awaiting_approval(update.callback_query)
    elif data == "buy_vip":
        buy_vip(update.callback_query)
    elif data == "back_to_menu":
        back_to_menu(update.callback_query)
    elif data == "add_to_awaiting":
        add_to_awaiting(update.callback_query)
    elif data == "add_to_users":
        add_to_users(update.callback_query)
    elif data == "delete_from_awaiting":
        delete_from_awaiting(update.callback_query)
        user_to_delete = update.message.text
        update.message.edit_text(f"Usunięto z listy: {user_to_delete}")


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    check_answer(query, update, context)


def delete_from_awaiting(update):
    """Deletes user from awaiting.csv file."""
    # TODO do usunięcia
    filename = "awaiting.csv"
    users = get_all_users(filename)
    user_to_delete = update.message.text
    for x in users:
        if x[1] == user_to_delete:
            users.remove(x)
    with open(filename, 'w+', newline='') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerows(users)
    update.message.edit_text(f"Usunięto z listy: {user_to_delete}")


def delete_from_awaiting_vip(data):
    """Deletes user from awaiting.csv file, may be when adding same user to vip group but not necessarily."""
    filename = "awaiting.csv"
    awaiting = get_all_users(filename)
    user_nick = data[1]
    for x in awaiting:
        if x[1] == user_nick:
            awaiting.remove(x)
    with open(filename, 'w+', newline='') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerows(awaiting)


def save_to_file(data, filename):
    """Save new user to file with users of file with users that awaits for vip."""
    all_records = get_all_users(filename)
    for record in all_records:
        if record[0] == int(data[0]):
            with open(filename, 'w+', newline='') as file:
                csvwriter = csv.writer(file)
                csvwriter.writerows(all_records)
                return True
    if not all_records:
        awaiting_id = data[0]
        awaiting_nick = data[1]
        awaiting_date = datetime.now()
        awaiting_is_admin = False
        first = [awaiting_id, awaiting_nick, awaiting_date, awaiting_is_admin]
        with open(filename, 'w+', newline='') as file:
            csvwriter = csv.writer(file)
            csvwriter.writerow(first)
            return
    with open(filename, 'a+', newline='') as file:
        csvwriter = csv.writer(file)
        csvwriter.writerow(data)
        return False


def add_to_users(update, user_id=0):
    """Add to users file (to vip group)."""
    awaiting = get_all_users("awaiting.csv")
    user_nick = update.message.text
    for x in awaiting:
        if x[1] == user_nick:
            awaiting.remove(x)
            user_id = x[0]
            is_admin = check_if_admin(user_id)
            try:
                user_date, user = check_user(user_id)
                vip_till = user_date + timedelta(days=30)
            except TypeError:
                vip_till = datetime.now()
                vip_till += timedelta(days=30)
            data = [str(user_id), str(user_nick), str(vip_till), str(is_admin)]
            filename = "users.csv"
            save_to_file(data, filename)
            delete_from_awaiting_vip(data)
            update.message.edit_text(f"{user_nick} dodano do VIP")
            update.bot.send_message(user_id, f"Zostałeś dodany do grupy VIP, "
                                             f"teraz wystarczy poczekać na nowe wiadomości ;)")


def check_user(user_id):
    """Checks if user is already in file, if that's the case then change the expiry date accordingly."""
    filename = "users.csv"
    users = []
    try:
        with open(filename, 'r') as file:
            csvreader = csv.reader(file)
            for row in csvreader:
                temp_user_id = int(row[0])
                user_nick = str(row[1])
                due_date = datetime.strptime(row[2], '%Y-%m-%d %H:%M:%S.%f')
                is_admin = eval(row[3])
                user = [temp_user_id, user_nick, due_date, is_admin]
                users.append(user)
        for user in users:
            if int(user[0]) == user_id:
                if user[3]:
                    return user[2], True
                else:
                    return user[2], False
        return False
    except:
        return False


dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(MessageHandler(Filters.text, send_message))
dispatcher.add_handler(MessageHandler(Filters.photo, send_picture))

updater.start_polling()
updater.idle()
