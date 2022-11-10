'''
  OnionPerf
  Authored by Rob Jansen, 2015
  Copyright 2015-2020 The Tor Project
  See LICENSE for licensing information
'''

import os, re, json, datetime, logging

from abc import ABCMeta, abstractmethod

# stem imports
from stem import CircEvent, CircStatus, CircPurpose, StreamStatus, GuardStatus, GuardType
from stem.response.events import CircuitEvent, CircMinorEvent, StreamEvent, BuildTimeoutSetEvent, GuardEvent
from stem.response import ControlMessage, convert

# tgentools imports
from tgentools.analysis import Analysis, TGenParser

# onionperf imports
from . import util

class OPAnalysis(Analysis):

    def __init__(self, nickname=None, ip_address=None):
        super().__init__(nickname, ip_address)
        self.json_db = {'type': 'onionperf', 'version': '3.1', 'data': {}}
        self.torctl_filepaths = []

    def add_torctl_file(self, filepath):
        self.torctl_filepaths.append(filepath)

    def analyze(self, date_filter=None, exclude_cbt=False):
        if self.did_analysis:
            return
        self.exclude_cbt = exclude_cbt
        if exclude_cbt:
            filters = self.json_db.setdefault("filters", {})
            tor_circuits_filters = filters.setdefault("tor/circuits", [])
            tor_circuits_filters.append({"name": "exclude_cbt"})
        self.date_filter = date_filter
        super().analyze(do_complete=True, date_filter=self.date_filter)
        torctl_parser = TorCtlParser(date_filter=self.date_filter, exclude_cbt=self.exclude_cbt)

        for (filepaths, parser, json_db_key) in [(self.torctl_filepaths, torctl_parser, 'tor')]:
            if len(filepaths) > 0:
                for filepath in filepaths:
                    logging.info("parsing log file at {0}".format(filepath))
                    parser.parse(util.DataSource(filepath))

                if self.nickname is None:
                    parsed_name = parser.get_name()
                    if parsed_name is not None:
                        self.nickname = parsed_name
                    elif self.hostname is not None:
                        self.nickname = self.hostname
                    else:
                        self.nickname = "unknown"

                if self.measurement_ip is None:
                    self.measurement_ip = "unknown"

                self.json_db['data'].setdefault(self.nickname, {'measurement_ip': self.measurement_ip}).setdefault(json_db_key, parser.get_data())
        self.json_db['data'][self.nickname]["tgen"].pop("heartbeats")
        self.json_db['data'][self.nickname]["tgen"].pop("init_ts")
        self.json_db['data'][self.nickname]["tgen"].pop("stream_summary")
        self.did_analysis = True

    def save(self, filename=None, output_prefix=os.getcwd(), do_compress=True, date_prefix=None, sort_keys=True):
        if filename is None:
            base_filename = "onionperf.analysis.json.xz"
            if date_prefix is not None:
                filename = "{0}.{1}".format(util.date_to_string(date_prefix), base_filename)
            elif self.date_filter is not None:
                filename = "{0}.{1}".format(util.date_to_string(self.date_filter), base_filename)
            else:
                filename = base_filename

        filepath = os.path.abspath(os.path.expanduser("{0}/{1}".format(output_prefix, filename)))
        if not os.path.exists(output_prefix):
            os.makedirs(output_prefix)

        logging.info("saving analysis results to {0}".format(filepath))

        outf = util.FileWritable(filepath, do_compress=do_compress)
        json.dump(self.json_db, outf, sort_keys=sort_keys, separators=(',', ': '), indent=2)
        outf.close()

        logging.info("done!")


    def get_tgen_streams(self, node):
        try:
            return self.json_db['data'][node]['tgen']['streams']
        except:
            return None

    def get_tgen_transfers(self, node):
        try:
            return self.json_db['data'][node]['tgen']['transfers']
        except:
            return None

    def get_tor_guards(self, node):
        try:
            return self.json_db['data'][node]['tor']['guards']
        except:
            return None

    def get_tor_circuits(self, node):
        try:
            return self.json_db['data'][node]['tor']['circuits']
        except:
            return None

    def set_tor_circuits(self, node, tor_circuits):
        self.json_db['data'][node]['tor']['circuits'] = tor_circuits

    def get_tor_streams(self, node):
        try:
            return self.json_db['data'][node]['tor']['streams']
        except:
            return None

    @classmethod
    def load(cls, filename="onionperf.analysis.json.xz", input_prefix=os.getcwd()):
        filepath = os.path.abspath(os.path.expanduser("{0}".format(filename)))
        if not os.path.exists(filepath):
            filepath = os.path.abspath(os.path.expanduser("{0}/{1}".format(input_prefix, filename)))
            if not os.path.exists(filepath):
                logging.warning("file does not exist at '{0}'".format(filepath))
                return None

        logging.info("loading analysis results from {0}".format(filepath))

        inf = util.DataSource(filepath)
        inf.open()
        db = json.load(inf.get_file_handle())
        inf.close()

        logging.info("done!")

        if 'type' not in db or 'version' not in db:
            logging.warning("'type' or 'version' not present in database")
            return None
        elif db['type'] != 'onionperf' or str(db['version']) >= '6.':
            logging.warning("type or version not supported (type={0}, version={1})".format(db['type'], db['version']))
            return None
        else:
            analysis_instance = cls()
            analysis_instance.json_db = db
            return analysis_instance

class Parser(object, metaclass=ABCMeta):
    @abstractmethod
    def parse(self, source):
        pass
    @abstractmethod
    def get_data(self):
        pass
    @abstractmethod
    def get_name(self):
        pass


class TorStream(object):
    def __init__(self, sid):
        self.stream_id = sid
        self.circuit_id = None
        self.unix_ts_start = None
        self.unix_ts_end = None
        self.failure_reason_local = None
        self.failure_reason_remote = None
        self.source = None
        self.target = None
        self.elapsed_seconds = []
        self.last_purpose = None

    def add_event(self, purpose, status, arrived_at):
        if purpose is not None:
            self.last_purpose = purpose
        key = "{0}:{1}".format(self.last_purpose, status)
        self.elapsed_seconds.append([key, arrived_at])

    def set_circ_id(self, circ_id):
        if circ_id is not None:
            self.circuit_id = circ_id

    def set_start_time(self, unix_ts):
        if self.unix_ts_start is None:
            self.unix_ts_start = unix_ts

    def set_end_time(self, unix_ts):
        self.unix_ts_end = unix_ts

    def set_local_failure(self, reason):
        self.failure_reason_local = reason

    def set_remote_failure(self, reason):
        self.failure_reason_remote = reason

    def set_target(self, target):
        self.target = target

    def set_source(self, source):
        self.source = source

    def get_data(self):
        if self.unix_ts_start is None or self.unix_ts_end is None:
            return None
        d = self.__dict__
        for item in d['elapsed_seconds']:
            item[1] = item[1] - self.unix_ts_start
        del(d['last_purpose'])
        if d['failure_reason_local'] is None: del(d['failure_reason_local'])
        if d['failure_reason_remote'] is None: del(d['failure_reason_remote'])
        if d['source'] is None: del(d['source'])
        if d['target'] is None: del(d['target'])
        return d

    def __str__(self):
        return('stream id=%d circ_id=%s %s' % (self.id, self.circ_id,
               ' '.join(['%s=%s' % (event, arrived_at)
               for (event, arrived_at) in sorted(self.elapsed_seconds, key=lambda item: item[1])])))

class TorCircuit(object):
    def __init__(self, cid):
        self.circuit_id = cid
        self.unix_ts_start = None
        self.unix_ts_end = None
        self.failure_reason_local = None
        self.failure_reason_remote = None
        self.buildtime_seconds = None
        self.build_timeout = None
        self.build_quantile = None
        self.cbt_set = False
        self.current_guards = None
        self.elapsed_seconds = []
        self.path = []

    def add_event(self, event, arrived_at):
        self.elapsed_seconds.append([str(event), arrived_at])

    def add_current_guards(self, guards):
        g = [guard.get_data() for guard in guards]
        self.current_guards = g

    def add_hop(self, hop, arrived_at):
        self.path.append(["${0}~{1}".format(hop[0], hop[1]), arrived_at])

    def set_launched(self, unix_ts, build_timeout, build_quantile, cbt_set):
        if self.unix_ts_start is None:
            self.unix_ts_start = unix_ts
        self.build_timeout = build_timeout
        self.build_quantile = build_quantile
        self.cbt_set = cbt_set

    def set_end_time(self, unix_ts):
        self.unix_ts_end = unix_ts

    def set_local_failure(self, reason):
        self.failure_reason_local = reason

    def set_remote_failure(self, reason):
        self.failure_reason_remote = reason

    def set_build_time(self, unix_ts):
        if self.buildtime_seconds is None:
            self.buildtime_seconds = unix_ts

    def get_data(self):
        if self.unix_ts_start is None or self.unix_ts_end is None:
            return None
        d = self.__dict__
        for item in d['elapsed_seconds']:
            item[1] = item[1] - self.unix_ts_start
        for item in d['path']:
            item[1] = item[1] - self.unix_ts_start
        if d['buildtime_seconds'] is None:
            del(d['buildtime_seconds'])
        else:
            d['buildtime_seconds'] = self.buildtime_seconds - self.unix_ts_start
        if len(d['path']) == 0: del(d['path'])
        d = {k: v for k, v in d.items() if v is not None}
        return d

    def __str__(self):
        return('circuit id=%d %s' % (self.id, ' '.join(['%s=%s' %
               (event, arrived_at) for (event, arrived_at) in
               sorted(self.elapsed_seconds, key=lambda item: item[1])])))

class TorGuard(object):
    def __init__(self, fingerprint, nickname, country=None):
        self.fingerprint = fingerprint
        self.nickname = nickname
        self.country = country
        self.new_ts = None
        self.up_ts = None
        self.down_ts = None
        self.dropped_ts = None

    def get_data(self):
        d = self.__dict__
        d = {k: v for k, v in d.items() if v is not None}
        return d

class TorCtlParser(Parser):

    def __init__(self, date_filter=None, exclude_cbt=False):
        ''' date_filter should be given in UTC '''
        self.circuits_state = {}
        self.circuits = {}
        self.streams_state = {}
        self.streams = {}
        self.guards = []
        self.name = None
        self.boot_succeeded = False
        self.build_timeout_last = None
        self.build_quantile_last = None
        self.cbt_set = False
        self.date_filter = date_filter
        self.exclude_cbt = exclude_cbt

    def __handle_circuit(self, event, arrival_dt):
        # first make sure we have a circuit object
        cid = int(event.id)
        circ = self.circuits_state.setdefault(cid, TorCircuit(cid))
        is_hs_circ = True if event.purpose in (CircPurpose.HS_CLIENT_INTRO, CircPurpose.HS_CLIENT_REND, \
                                   CircPurpose.HS_SERVICE_INTRO, CircPurpose.HS_SERVICE_REND) else False

        # now figure out what status we want to track
        key = None
        if isinstance(event, CircuitEvent):
            if event.status == CircStatus.LAUNCHED:
                circ.set_launched(arrival_dt, self.build_timeout_last, self.build_quantile_last, self.cbt_set)

            key = "{0}:{1}".format(event.purpose, event.status)
            circ.add_event(key, arrival_dt)

            if event.status == CircStatus.EXTENDED:
                circ.add_hop(event.path[-1], arrival_dt)
            elif event.status == CircStatus.FAILED:
                circ.set_local_failure(event.reason)
                if event.remote_reason is not None and event.remote_reason != '':
                    circ.set_remote_failure(event.remote_reason)
            elif event.status == CircStatus.BUILT:
                circ.set_build_time(arrival_dt)
                if is_hs_circ:
                    key = event.hs_state
                    if event.rend_query is not None and event.rend_query != '':
                        key = "{0}:{1}".format(key, event.rend_query)
                    circ.add_event(key, arrival_dt)

            if event.status == CircStatus.CLOSED or event.status == CircStatus.FAILED:
                current_guards = []
                for g in self.guards:
                    if g.up_ts and circ.unix_ts_start >= g.up_ts and (not g.dropped_ts or circ.unix_ts_start < g.dropped_ts):
                        current_guards.append(g)
                if current_guards:
                    circ.add_current_guards(current_guards)
                circ.set_end_time(arrival_dt)
                started, built, ended = circ.unix_ts_start, circ.buildtime_seconds, circ.unix_ts_end

                data = circ.get_data()
                if data is not None:
                    if self.exclude_cbt and data["cbt_set"] == False:
                       data['filtered_out'] = True
                    else:
                       data['filtered_out'] = False
                    self.circuits[cid] = data
                self.circuits_state.pop(cid)

        elif isinstance(event, CircMinorEvent):
            if event.purpose != event.old_purpose or event.event != CircEvent.PURPOSE_CHANGED:
                key = "{0}:{1}".format(event.event, event.purpose)
                circ.add_event(key, arrival_dt)

            if is_hs_circ:
                key = event.hs_state
                if event.rend_query is not None and event.rend_query != '':
                    key = "{0}:{1}".format(key, event.rend_query)
                circ.add_event(key, arrival_dt)

    def __handle_stream(self, event, arrival_dt):
        sid = int(event.id)
        strm = self.streams_state.setdefault(sid, TorStream(sid))

        if event.circ_id is not None:
            strm.set_circ_id(event.circ_id)

        strm.add_event(event.purpose, event.status, arrival_dt)
        strm.set_target(event.target)

        if event.status == StreamStatus.NEW or event.status == StreamStatus.NEWRESOLVE:
            strm.set_start_time(arrival_dt)
            strm.set_source(event.source_addr)
        elif event.status == StreamStatus.FAILED:
            strm.set_local_failure(event.reason)
            if event.remote_reason is not None and event.remote_reason != '':
                strm.set_remote_failure(event.remote_reason)

        if event.status == StreamStatus.CLOSED or event.status == StreamStatus.FAILED:
            strm.set_end_time(arrival_dt)
            stream_type = strm.last_purpose
            started, ended = strm.unix_ts_start, strm.unix_ts_end

            data = strm.get_data()
            if data is not None:
                self.streams[sid] = data
            self.streams_state.pop(sid)

    def __handle_buildtimeout(self, event, arrival_dt):
        if event.set_type == 'RESET':
           self.cbt_set = False
        else:
           self.cbt_set = True
        self.build_timeout_last = event.timeout
        self.build_quantile_last = event.quantile

    def __handle_guard(self, event, arrival_dt):
        if event.guard_type != GuardType.ENTRY:
            return
        elif event.status == "GOOD_L2":
            return
        elif event.status == "BAD_L2":
            return
        else:
            pass
        fingerprint = event.endpoint_fingerprint
        nickname = event.endpoint_nickname
        guard = None
        for g in reversed(self.guards):
            if g.fingerprint == fingerprint:
                guard = g
                break
        if guard is None or guard.dropped_ts is not None:
            try:
                country = util.get_country_by_fingerprint(fingerprint)
            except IndexError:
                pass
            guard = TorGuard(fingerprint=fingerprint, nickname=nickname, country=country)
            self.guards.append(guard)
        if event.status == GuardStatus.NEW and guard.new_ts is None:
            guard.new_ts = arrival_dt
        elif event.status == GuardStatus.UP and guard.up_ts is None:
            guard.up_ts = arrival_dt
        elif event.status == GuardStatus.DOWN and guard.down_ts is None:
            guard.down_ts = arrival_dt
        elif event.status == GuardStatus.DROPPED and guard.dropped_ts is None:
            guard.dropped_ts = arrival_dt

    def __handle_event(self, event, arrival_dt):
        if isinstance(event, (CircuitEvent, CircMinorEvent)):
            self.__handle_circuit(event, arrival_dt)
        elif isinstance(event, StreamEvent):
            self.__handle_stream(event, arrival_dt)
        elif isinstance(event, BuildTimeoutSetEvent):
            self.__handle_buildtimeout(event, arrival_dt)
        elif isinstance(event, GuardEvent):
            self.__handle_guard(event, arrival_dt)

    def __is_date_valid(self, date_to_check):
        if self.date_filter is None:
            # we are not asked to filter, so every date is valid
            return True
        else:
            # we are asked to filter, so the line is only valid if the date matches the filter
            # both the filter and the unix timestamp should be in UTC at this point
            return util.do_dates_match(self.date_filter, date_to_check)

    def __parse_line(self, line):
        if not self.boot_succeeded:
            if re.search("Starting\storctl\sprogram\son\shost", line) is not None:
                parts = line.strip().split()
                if len(parts) < 11:
                    return True
                self.name = parts[10]
            if re.search("Bootstrapped\s100", line) is not None:
                self.boot_succeeded = True
            elif re.search("BOOTSTRAP", line) is not None and re.search("PROGRESS=100", line) is not None:
                self.boot_succeeded = True

        # parse with stem
        timestamps, sep, raw_event_str = line.partition(" 650 ")
        if sep == '':
            return True

        # event.arrived_at is also available but at worse granularity
        unix_ts = float(timestamps.strip().split()[2])

        # check if we should ignore the line
        line_date = datetime.datetime.utcfromtimestamp(unix_ts).date()
        if not self.__is_date_valid(line_date):
            return True

        event = ControlMessage.from_str("{0} {1}".format(sep.strip(), raw_event_str))
        convert('EVENT', event)
        self.__handle_event(event, unix_ts)

        return True

    def parse(self, source):
        source.open(newline='\r\n')
        for line in source:
            # ignore line parsing errors
            try:
                if self.__parse_line(line):
                    continue
                else:
                    break
            except:
                continue
        source.close()

    def get_data(self):
        return {'circuits': self.circuits, 'streams': self.streams,
                'guards': [guard.get_data() for guard in self.guards]}

    def get_name(self):
        return self.name
