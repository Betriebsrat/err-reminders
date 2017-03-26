import uuid
import parsedatetime
import pytz
from datetime import datetime
from errbot import BotPlugin, botcmd
from pytz import utc

__author__ = 'kdknowlton, Betriebsrat'

DEFAULT_POLL_INTERVAL = 60  # one minute
DEFAULT_LOCALE = 'en_US'  # CHANGE THIS TO YOUR LOCALE


class RemindMe(BotPlugin):
    min_err_version = '4.1.3'

    # Configuration
    def configure(self, configuration):
        if configuration:
            if type(configuration) != dict:
                raise Exception('Wrong configuration type')
            if 'POLL_INTERVAL' not in configuration:
                raise Exception('Wrong configuration type, it should contain POLL_INTERVAL')
            if 'LOCALE' not in configuration:
                raise Exception('Wrong configuration type, it should contain LOCALE')
            if len(configuration) > 2:
                raise Exception('What else did you try to insert in my config ?')
            try:
                int(configuration['POLL_INTERVAL'])
                str(configuration['LOCALE'])
            except:
                raise Exception('Configuration Error')
        super(RemindMe, self).configure(configuration)

    def get_configuration_template(self):
        return {'POLL_INTERVAL': DEFAULT_POLL_INTERVAL, 'LOCALE': DEFAULT_LOCALE}

    def activate(self):
        super(RemindMe, self).activate()
        self.send_reminders()
        self.start_poller(
            self.config['POLL_INTERVAL'] if self.config else DEFAULT_POLL_INTERVAL,
            self.send_reminders
        )

    def store_reminder(self, reminder):
        reminders = self.get('reminders', {})
        reminders[reminder['id']] = reminder
        self['reminders'] = reminders

    def remove_reminder(self, reminderId):
        reminders = self['reminders']
        del reminders[reminderId]
        self['reminders'] = reminders

    def add_reminder(self, date, nick, message, target, is_user=True):
        reminder = {
            "id": uuid.uuid4().hex,
            "date": date,
            "message": message,
            "target": target,
            "is_user": is_user,
            "nick": nick,
        }
        self.store_reminder(reminder)
        return reminder

    def get_all_reminders(self):
        return self.get('reminders', {}).values()

    def send_reminders(self):
        for reminder in self.get_all_reminders():
            if pytz.utc.localize(datetime.now()) > reminder['date']:
                self.send(
                    self.build_identifier(reminder['target']),
                    "{nick} , here is your reminder: {message}".format(nick=reminder['nick'],
                                                                       message=reminder['message']),
                )
                self.remove_reminder(reminder['id'])

    @botcmd(split_args_with='::')
    def remind_me(self, msg, args):
        """Takes a message of the form of '!remind me [when] :: [what]' and stores the reminder. Usage: !remind me <date/time> :: <thing>"""
        if len(args) != 2:
            return "Usage: !remind me <date/time> :: <thing>"

        pdt = parsedatetime.Calendar(parsedatetime.Constants(self.config['LOCALE'] if self.config else DEFAULT_LOCALE))
        date_string = args[0]
        date_struct = pdt.parse(date_string, datetime.now(utc).timetuple())
        if date_struct[1] != 0:
            date = pytz.utc.localize(datetime(*(date_struct[0])[:6]))
            message = args[1]
            nick = msg.frm.nick
            target = str(msg.frm) if msg.is_direct else str(msg.to)
            self.add_reminder(date, nick, message, target, msg.is_direct)
            return "Reminder set to \"{message}\" at {date}.".format(message=message, date=date)
        else:
            return "Your date seems malformed: {date}".format(date=date_string)

    @botcmd(admin_only=True)
    def remind_clearall(self, mess, args):
        """WARNING: This will clear all reminders for all users and rooms!"""
        self['reminders'] = {}
        return 'All reminders have been cleared.'
