import uuid
from datetime import datetime

import parsedatetime
import pytz
from errbot import BotPlugin, botcmd
from pytz import utc
import html
import sys

__author__ = 'kdknowlton, Betriebsrat'

DEFAULT_POLL_INTERVAL = 60  # one minute
DEFAULT_LOCALE = 'en_US'  # CHANGE THIS TO YOUR LOCALE


class RemindMe(BotPlugin):
    min_err_version = '4.7.3'

    def get_configuration_template(self):
        return {'POLL_INTERVAL': DEFAULT_POLL_INTERVAL, 'LOCALE': DEFAULT_LOCALE}

    def activate(self):
        self.start_poller(
            self.config['POLL_INTERVAL'] if self.config else DEFAULT_POLL_INTERVAL,
            self.send_reminders
        )
        super().activate()

    def set_reminder(self, date, nick, message, target, is_user=True):
        """stores reminder in internal dictionary"""
        uid = uuid.uuid4().hex
        if uid not in self:
            self[uid] = {}
        with self.mutable(uid) as d:
            d['nick'] = nick
            d['date'] = date
            d['message'] = message
            d['target'] = target
            d['is_user'] = is_user

    def send_reminders(self):
        for item in self:
            if pytz.utc.localize(datetime.now()) > self[item]['date']:
                self.send(
                    self.build_identifier(self[item]['target']),
                    "{nick} , here is your reminder: {message}".format(nick=self[item]['nick'],
                                                                       message=self[item]['message']),
                )
                del self[item]

    @botcmd(split_args_with=html.escape('->') if 'slackclient' in sys.modules else '->')
    def remind_me(self, msg, args):
        """Takes a message of the form of '!remind me [when] -> [what]' and stores the reminder. Usage: !remind me <date/time> -> <thing>"""
        if len(args) != 2:
            return "Usage: !remind me <date/time> -> <thing>"

        pdt = parsedatetime.Calendar(parsedatetime.Constants(self.config['LOCALE'] if self.config else DEFAULT_LOCALE))
        date_string = args[0]
        date_struct = pdt.parse(date_string, datetime.now(utc).timetuple())
        if date_struct[1] != 0:
            date = pytz.utc.localize(datetime(*(date_struct[0])[:6]))
            message = args[1]
            nick = msg.frm.nick
            target = str(msg.frm) if msg.is_direct else str(msg.to)
            self.set_reminder(date, nick, message, target, msg.is_direct)
            return "Reminder set to \"{message}\" at {date}.".format(message=message, date=date)
        else:
            return "Your date seems malformed: {date}".format(date=date_string)

    @botcmd(admin_only=True)
    def remind_clearall(self, msg, args):
        """WARNING: This will clear all reminders for all users and rooms!"""
        for item in self:
            del self[item]
        return 'All reminders have been cleared.'
