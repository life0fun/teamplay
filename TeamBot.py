#!/usr/bin/env python

"""
This class periodical sched to run that wake up bot and send message.
"""
import sys
import logging
import getpass
import ConfigParser
from optparse import OptionParser
from ConfigParser import SafeConfigParser

from apscheduler.scheduler import Scheduler

import sleekxmpp

from statslog import StatsLog

# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input


''' schedule as global variable and start it '''
sched = Scheduler()
sched.start()

"""
    configuration info
"""
class TeamConfiguration(object):
    def __init__(self, configfile='team.cfg'):
        self.parser = SafeConfigParser()
        self.parser.read(configfile)

    def getGtalkServer(self):
        return self.parser.get('bot', 'gtalk')

    def getBotId(self):
        return self.parser.get('bot', 'jid'), self.parser.get('bot', 'passwd')

    def getTeamMember(self):
        print self.parser.items('team_member')
        return self.parser.items('team_member')

    def useProxy(self):
        return True if self.parser.get('proxy', 'use_proxy') in ['true', '1', 't', 'y', 'yes'] else False

    def getProxyInfo(self):
        return self.parser.get('proxy', 'proxy_host'), \
               self.parser.get('proxy', 'proxy_port'), \
               self.parser.get('proxy', 'proxy_user'), \
               self.parser.get('proxy', 'proxy_pass')


    def getDayOfWeek(self):
        return self.parser.get('schedule', 'day_of_week')

    def getHour(self):
        return self.parser.get('schedule', 'hour')

    def getMinute(self):
        return self.parser.get('schedule', 'minute')

    ''' keep inc index until exception when idx out of question range '''
    def getQuestion(self, idx):
        try:
            q = self.parser.get('questions', idx)
        except ConfigParser.Error:
            return None
        return q

"""
    this class encap staff state
"""
class StaffState(object):
    def __init__(self):
        ''' the state incl  question, time '''
        self.staffstate = {}

    def getQuestionState(self, name):
        return self.staffstate.get(name).get('question')

    def updateQuestionState(self, name, qidx):
        self.staffstate.setdefault(name, {}).update(dict({'question':qidx}))

    def updateTimeState(self, name, tot):
        self.staffstate.setdefault(name, {}).update(dict({'time':tot}))

"""
    Bot the periodically send collect stats msg to staff list
"""
class TeamBot(sleekxmpp.ClientXMPP):
    #GtalkServer = '74.125.142.125'

    ''' use DepInj so we can easy test '''
    def __init__(self, configfile='team.cfg'):
        self.configuration = TeamConfiguration(configfile)

        self.Jid, self.Password = self.configuration.getBotId()

        sleekxmpp.ClientXMPP.__init__(self, self.Jid, self.Password)

        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0199') # XMPP Ping

        self.logger = StatsLog()

        self.staffstate = StaffState()

        # The session_start event will be triggered when
        # the bot establishes its connection with the server
        # and the XML streams are ready for use. We want to
        # listen for this event so that we we can initialize
        # our roster.
        self.add_event_handler('connected', self.connected)
        self.add_event_handler('disconnected', self.disconnected)

        self.add_event_handler('presence_available', self.available)
        self.add_event_handler('presence_unavailable', self.unavailable)

        self.add_event_handler("session_start", self.sessionStart, threaded=True)
        #self.add_event_handler("message", self.messageCB())
        self.add_event_handler("message", self.message)

    def connected(self, event=None):
        self.logger.logConsole('connected...')

    def disconnected(self, event=None):
        self.logger.logConsole('disconnected...re-connected GTalk server')
        self.connectToGtalk()

    def available(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.logger.logConsole('presence available : ' + pto + ' from: ' + pfrom)

    def unavailable(self, presence):
        pto = presence['to'].bare
        pfrom = presence['from'].bare
        self.logger.logConsole('presence unavailable : ' + pto + ' from: ' + pfrom)

    """ connect to GTalk thru tls http proxying wwwgate0.mot """
    def connectToGtalk(self):
        gtalk = self.configuration.getGtalkServer()
        self.use_proxy = self.configuration.useProxy()
        if self.use_proxy:
            print 'use proxy', self.use_proxy
            #raise AssertionError, 'use proxy wrong'
            h,p,u,pwd = self.configuration.getProxyInfo()
            self.proxy_config = {
                'host': h,
                'port': int(p),
                'username': u,
                'password': pwd}

        if self.connect((gtalk, 5222), True, True, False):
            self.process(block=True)
            print("Done")
        else:
            print("Unable to connect.")

    """ the main entry point of bot logic """
    def sessionStart(self, event):
        """
        Process the session_start event.

        Typical actions for the session_start event are
        requesting the roster and broadcasting an initial
        presence stanza.
        """
        self.send_presence()
        self.get_roster()

        day = self.configuration.getDayOfWeek()
        hour = self.configuration.getHour()
        minute = self.configuration.getMinute()

        # add schedule cron job
        sched.add_cron_job(self.collectStats, day_of_week=day, hour=hour, minute=minute)

        # Using wait=True ensures that the send queue will be
        # emptied before ending the session.
        #self.disconnect(wait=True)
        self.collectStats()

    #@sched.cron_schedule(day_of_week='mon-sat', hour='10-17', minute=12)
    def collectStats(self):
        memlist = self.configuration.getTeamMember()
        for name,jid in memlist:
            self.staffstate.updateQuestionState(name, '1')   # first question
            self.sendMsg(jid, self.configuration.getQuestion('1'))

    # send msg to jid
    def sendMsg(self, toid, msg):
        self.logger.logConsole('sending msg to : ' + toid + ' : ' + msg)
        self.send_message(mto=toid, mbody=msg, mtype='chat')

    def message(self, msg):
        """
        Process incoming message stanzas. Be aware that this also
        includes MUC messages and error messages. It is usually
        a good idea to check the messages's type before processing
        or sending replies.

        Arguments:
            msg -- The received message stanza. See the documentation
                   for stanza objects and the Message stanza to see
                   how it may be used.
        """
        if msg['type'] in ('chat', 'normal'):
            from_id = str(msg['from']).split('@')[0]
            to_id = msg['to']
            body = msg['body']
            print 'message : ', from_id, ' -> ', to_id, ' :: ', body
            self.logger.logFile(from_id, body)
            #msg.reply("Thanks for sending status!\n%(body)s" % msg).send()
            nextqidx, nextq = self.getNextQuestion(from_id)
            if nextq is not None:
                self.staffstate.updateQuestionState(from_id, nextqidx)   # first question
                msg.reply("Thanks!\n%s" % nextq).send()

    def messageCB(self):
        def cb(msg):
            if msg['type'] in ('chat', 'normal'):
                from_id = str(msg['from']).split('@')[0]  # need to convert to string
                to_id = msg['to']
                body = msg['body']
                print 'cb log msg: ', from_id, ' -> ', to_id, ' :: ', body
                self.logger.logFile(from_id, body)
                msg.reply("Thanks for sending status!\n%(body)s" % msg).send()
        return cb

    def getNextQuestion(self, name):
        qidx = int(self.staffstate.getQuestionState(name))
        return str(qidx+1), self.configuration.getQuestion(str(qidx+1))

if __name__ == '__main__':

    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    optp.add_option("-p", "--password", dest="password", help="password to proxy")

    opts, args = optp.parse_args()

    #if opts.password is None:
    #    opts.password = getpass.getpass("wwwgate0 Password, or return for default: ")

    # Setup logging.
    logging.basicConfig(level=opts.loglevel, format='%(levelname)-8s %(message)s')

    xmpp = TeamBot()
    xmpp.connectToGtalk()
