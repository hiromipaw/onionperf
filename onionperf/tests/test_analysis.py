import json
import lzma
import os
import pkg_resources
from nose.tools import *
from onionperf import util
from onionperf.analysis import OPAnalysis, TorCtlParser
from tgentools import analysis


def absolute_data_path(relative_path=""):
    """
    Returns an absolute path for test data given a relative path.
    """
    return pkg_resources.resource_filename("onionperf",
                                           "tests/data/" + relative_path)

DATA_DIR = absolute_data_path()
LINE_ERROR = '2019-04-22 14:41:20 1555940480.647663 [message] [tgen-stream.c:1618] [_tgenstream_log] [stream-error] transport [fd=12,local=localhost:127.0.0.1:46878,proxy=localhost:127.0.0.1:43735,remote=dc34og3c3aqdqntblnxkstzfvh7iy7llojd4fi5j23y2po32ock2k7ad.onion:0.0.0.0:8080,state=ERROR,error=READ] stream [id=4,vertexid=stream5m,name=cyan,peername=(null),sendsize=0,recvsize=5242880,sendstate=SEND_COMMAND,recvstate=RECV_NONE,error=PROXY] bytes [total-bytes-recv=0,total-bytes-send=0,payload-bytes-recv=0,payload-bytes-send=0,payload-progress-recv=0.00%,payload-progress-send=100.00%] times [created-ts=5948325159988,usecs-to-socket-create=11,usecs-to-socket-connect=210,usecs-to-proxy-init=283,usecs-to-proxy-choice=348,usecs-to-proxy-request=412,usecs-to-proxy-response=-1,usecs-to-command=-1,usecs-to-response=-1,usecs-to-first-byte-recv=-1,usecs-to-last-byte-recv=-1,usecs-to-checksum-recv=-1,usecs-to-first-byte-send=-1,usecs-to-last-byte-send=-1,usecs-to-checksum-send=-1,now-ts=5948446579043]'

NO_PARSE_LINE = '2018-04-14 21:10:04 1523740204.809894 [message] [tgen-stream.c:1618] [_tgenstream_log] [stream-error] transport [fd=17,local=localhost:127.0.0.1:46878,proxy=localhost:127.0.0.1:43735,remote=dc34og3c3aqdqntblnxkstzfvh7iy7llojd4fi5j23y2po32ock2k7ad.onion:0.0.0.0:8080,state=SUCCESS,error=NONE] stream [id=4,vertexid=stream5m,name=cyan,peername=(null),sendsize=0,recvsize=5242880,sendstate=SEND_COMMAND,recvstate=RECV_NONE,error=PROXY] bytes [total-bytes-recv=1,total-bytes-send=0,payload-bytes-recv=0,payload-bytes-send=0,payload-progress-recv=0.00%,payload-progress-send=100.00%] times [created-ts=5948325159988,usecs-to-socket-create=0,usecs-to-socket-connect=210,usecs-to-proxy-init=-1,usecs-to-proxy-choice=-1,usecs-to-proxy-request=-1,usecs-to-proxy-response=-1,usecs-to-command=-1,usecs-to-response=-1,usecs-to-first-byte-recv=-1,usecs-to-last-byte-recv=-1,usecs-to-checksum-recv=-1,usecs-to-first-byte-send=-1,usecs-to-last-byte-send=-1,usecs-to-checksum-send=-1,now-ts=5948446579043]'


def test_stream_status_event():
    stream = analysis.StreamStatusEvent(LINE_ERROR)
    assert_equals(stream.is_success, False)
    assert_equals(stream.is_error, False)
    assert_equals(stream.is_complete, False)
    assert_equals(stream.unix_ts_end, 1555940480.647663)
    assert_equals(stream.transport_info['local'], 'localhost:127.0.0.1:46878')
    assert_equals(stream.transport_info['proxy'], 'localhost:127.0.0.1:43735')
    assert_equals(
        stream.transport_info['remote'],
        'dc34og3c3aqdqntblnxkstzfvh7iy7llojd4fi5j23y2po32ock2k7ad.onion:0.0.0.0:8080'
    )
    assert_equals(stream.stream_id, '4:12:localhost:127.0.0.1:46878:dc34og3c3aqdqntblnxkstzfvh7iy7llojd4fi5j23y2po32ock2k7ad.onion:0.0.0.0:8080')
    assert_equals(stream.stream_info['name'], 'cyan')
    assert_equals(stream.stream_info['recvsize'], '5242880')
    assert_equals(stream.stream_info['peername'], '(null)')
    assert_equals(stream.stream_info['error'], 'PROXY')
    assert_equals(stream.byte_info['total-bytes-recv'], '0')
    assert_equals(stream.byte_info['total-bytes-send'], '0')
    assert_equals(stream.byte_info['payload-bytes-recv'], '0')


def test_stream_complete_event_init():
    complete = analysis.StreamCompleteEvent(LINE_ERROR)
    assert_equals(complete.is_complete, True)
    assert_equals(complete.time_info['usecs-to-proxy-init'], '283')
    assert_equals(complete.time_info['usecs-to-proxy-request'], '412')
    assert_equals(complete.time_info['usecs-to-proxy-choice'], '348')
    assert_equals(complete.time_info['usecs-to-socket-connect'], '210')
    assert_equals(complete.time_info['usecs-to-socket-create'], '11')
    assert_equals(complete.unix_ts_start, 1555940359.2286081)


def test_stream_error_event():
    error = analysis.StreamErrorEvent(LINE_ERROR)
    assert_equals(error.is_error, True)
    assert_equals(error.is_success, False)


def test_stream_success_event_init():
    success = analysis.StreamSuccessEvent(LINE_ERROR)
    assert_equals(success.is_success, True)


def test_stream_object_init():
    error = analysis.StreamErrorEvent(LINE_ERROR)
    s = analysis.Stream(error.stream_id)
    assert_equals(s.id, '4:12:localhost:127.0.0.1:46878:dc34og3c3aqdqntblnxkstzfvh7iy7llojd4fi5j23y2po32ock2k7ad.onion:0.0.0.0:8080')
    assert_equals(s.last_event, None)


def test_stream_object_add_event():
    error = analysis.StreamErrorEvent(LINE_ERROR)
    s = analysis.Stream(error.stream_id)
    s.add_event(error)
    assert_equals(s.last_event, error)


@raises(KeyError)
def test_stream_object_get_data_error():
    error = analysis.StreamErrorEvent(LINE_ERROR)
    s = analysis.Stream(error.stream_id)
    s.add_event(error)
    s.get_data()['elapsed_seconds']['payload_progress_recv']


def test_stream_object_get_data_no_error():
    success = analysis.StreamSuccessEvent(LINE_ERROR)
    s = analysis.Stream(success.stream_id)
    s.add_event(success)
    assert_true(
        s.get_data()['elapsed_seconds']['payload_progress_recv'] is not None)


def test_stream_object_end_to_end():
    error = analysis.StreamErrorEvent(LINE_ERROR)
    s = analysis.Stream(error.stream_id)
    s.add_event(error)
    assert_equals(
        s.get_data(), {
            'is_success': False,
            'is_error': True,
            'is_complete': True,
            'unix_ts_end': 1555940480.647663,
            'transport_info': {'fd': '12',
                'local': 'localhost:127.0.0.1:46878',
                'proxy': 'localhost:127.0.0.1:43735',
                'remote': 'dc34og3c3aqdqntblnxkstzfvh7iy7llojd4fi5j23y2po32ock2k7ad.onion:0.0.0.0:8080',
                'state': 'ERROR',
                'error': 'READ'},
            'stream_info': {
                'id': '4',
                'vertexid': 'stream5m',
                'name': 'cyan',
                'peername': '(null)',
                'sendsize': '0',
                'recvsize': '5242880',
                'sendstate': 'SEND_COMMAND',
                'recvstate': 'RECV_NONE',
                'error': 'PROXY'
            },
            'byte_info': {
                'total-bytes-recv': '0',
                'total-bytes-send': '0',
                'payload-bytes-recv': '0',
                'payload-bytes-send': '0',
                'payload-progress-recv': '0.00%',
                'payload-progress-send': '100.00%'
            },
            'time_info': {
                'created-ts': '5948325159988',
                'usecs-to-socket-create': '11',
                'usecs-to-socket-connect': '210',
                'usecs-to-proxy-init': '283',
                'usecs-to-proxy-choice': '348',
                'usecs-to-proxy-request': '412',
                'usecs-to-proxy-response': '-1',
                'usecs-to-command': '-1',
                'usecs-to-response': '-1',
                'usecs-to-first-byte-recv': '-1',
                'usecs-to-last-byte-recv': '-1',
                'usecs-to-checksum-recv': '-1',
                'usecs-to-first-byte-send': '-1',
                'usecs-to-last-byte-send': '-1',
                'usecs-to-checksum-send': '-1',
                'now-ts': '5948446579043'
            },
            'stream_id': '4:12:localhost:127.0.0.1:46878:dc34og3c3aqdqntblnxkstzfvh7iy7llojd4fi5j23y2po32ock2k7ad.onion:0.0.0.0:8080',
            'unix_ts_start': 1555940359.2286081
        })

def test_parsing_parse_error():
    parser = analysis.TGenParser()
    parser.parse(util.DataSource(DATA_DIR + 'parse_error'))

def test_handle_buildtimeout():
    parser = TorCtlParser(exclude_cbt=True)
    line = "2019-01-10 14:45:06 1547131506.44 650 BUILDTIMEOUT_SET COMPUTED TOTAL_TIMES=205 TIMEOUT_MS=1500 XM=225 ALPHA=2.060204 CUTOFF_QUANTILE=0.800000 TIMEOUT_RATE=0.009804 CLOSE_MS=60000 CLOSE_RATE=0.000000\r\n"
    parser._TorCtlParser__parse_line(line)
    assert_true(parser.cbt_set)

def test_exclude_cbt_option():
    analysis = OPAnalysis()
    analysis.add_tgen_file(absolute_data_path("logs/onionperf.tgen.log"))
    analysis.add_torctl_file(absolute_data_path("logs/onionperf.torctl.log"))
    analysis.analyze(exclude_cbt=True)
    analysis.save(output_prefix=absolute_data_path("analyses"))
    xz_file = lzma.open(absolute_data_path("analyses/onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_equals(json_content["filters"], json.loads('{"tor/circuits": [{"name": "exclude_cbt"}]}'))

def test_exclude_cbt_option_default():
    analysis = OPAnalysis()
    analysis.add_tgen_file(absolute_data_path("logs/onionperf.tgen.log"))
    analysis.add_torctl_file(absolute_data_path("logs/onionperf.torctl.log"))
    analysis.analyze()
    analysis.save(output_prefix=absolute_data_path("analyses"))
    xz_file = lzma.open(absolute_data_path("analyses/onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_false(json_content.get("filters"))
