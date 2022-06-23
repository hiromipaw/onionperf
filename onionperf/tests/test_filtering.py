import json
import lzma
import pkg_resources

from nose.tools import *
from onionperf.filtering import Filtering

def absolute_data_path(relative_path=""):
    """
    Returns an absolute path for test data given a relative path.
    """
    return pkg_resources.resource_filename("onionperf",
                                           "tests/data/" + relative_path)

def test_exclude_cbt_option():
    filtering = Filtering()
    filtering.exclude_cbt = True
    input_path = absolute_data_path("analyses/2021-06-01.op-hk6a.onionperf.analysis_no_filters.json.xz")
    output_dir = absolute_data_path("analyses/")
    output_file = "filtered-onionperf.analysis.json.xz"
    filtering.apply_filters(input_path=input_path, output_dir=output_dir, output_file=output_file)
    xz_file = lzma.open(absolute_data_path("analyses/filtered-onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_equals(json_content["filters"], json.loads('{"tor/circuits": [{"name": "exclude_cbt"}]}'))
    circuit_id = "177922"
    measurements = json_content['data']['op-hk6a']['tor']['circuits'][circuit_id]
    assert_false(measurements['cbt_set'])
    assert_true(measurements['filtered_out'])

def test_exclude_fingerprints():
    filtering = Filtering()
    fingerprint = "EB23FAE148CE2CAA7149525F1D533759E4EAB30E"
    filtering.fingerprints_to_exclude = []
    filtering.fingerprints_to_exclude.append(fingerprint)
    filtering.fingerprints_to_exclude_path = absolute_data_path("analyses/fingerprints.txt")
    input_path = absolute_data_path("analyses/2021-06-01.op-hk6a.onionperf.analysis_no_filters.json.xz")
    output_dir = absolute_data_path("analyses/")
    output_file = "filtered-fp-onionperf.analysis.json.xz"
    filtering.apply_filters(input_path=input_path, output_dir=output_dir, output_file=output_file)
    xz_file = lzma.open(absolute_data_path("analyses/filtered-fp-onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_equals(json_content["filters"]["tor/circuits"][0]["name"], "exclude_fingerprints")
    circuit_id = "177922"
    measurements = json_content['data']['op-hk6a']['tor']['circuits'][circuit_id]
    assert_true(measurements['filtered_out'])

def test_exclude_guards():
    guard = "A96DA63E4415E776FBFCCF3DA7154C804534B6E7"
    guard_circuit_id = "177923"
    fingerprint = "9E639C45F9AF3C9096B4BFA34DEACF1B1DA41766"
    circuit_id = "183977"
    filtering = Filtering()
    filtering.guards = True
    filtering.fingerprints_to_exclude = []
    filtering.fingerprints_to_exclude.append(guard)
    filtering.fingerprints_to_exclude.append(fingerprint)
    filtering.fingerprints_to_exclude_path = absolute_data_path("analyses/guards-fingerprints.txt")
    input_path = absolute_data_path("analyses/2021-06-01.op-hk6a.onionperf.analysis_no_filters.json.xz")
    output_dir = absolute_data_path("analyses/")
    output_file = "filtered-guards-onionperf.analysis.json.xz"
    filtering.apply_filters(input_path=input_path, output_dir=output_dir, output_file=output_file)
    xz_file = lzma.open(absolute_data_path("analyses/filtered-guards-onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_equals(json_content["filters"]["tor/circuits"][0]["name"], "exclude_fingerprints")
    measurements = json_content['data']['op-hk6a']['tor']['circuits'][circuit_id]
    assert_false(measurements['filtered_out'])
    guard_measurements = json_content['data']['op-hk6a']['tor']['circuits'][guard_circuit_id]
    assert_true(guard_measurements['filtered_out'])

def test_exclude_exits():
    exit_fp = "7AFC157269130BCF36BCCAC0F2DAA0685E70D40D"
    exit_circuit_id = "177926"
    fingerprint = "9E639C45F9AF3C9096B4BFA34DEACF1B1DA41766"
    circuit_id = "183977"
    onion_fp = "6D0D610D63D33584308CA672484DA699FF26A2A3"
    onion_circuit_id = "177929"
    filtering = Filtering()
    filtering.exits = True
    filtering.fingerprints_to_exclude = []
    filtering.fingerprints_to_exclude.append(exit_fp)
    filtering.fingerprints_to_exclude.append(fingerprint)
    filtering.fingerprints_to_exclude.append(onion_fp)
    filtering.fingerprints_to_exclude_path = absolute_data_path("analyses/exits-fingerprints.txt")
    input_path = absolute_data_path("analyses/2021-06-01.op-hk6a.onionperf.analysis_no_filters.json.xz")
    output_dir = absolute_data_path("analyses/")
    output_file = "filtered-exits-onionperf.analysis.json.xz"
    filtering.apply_filters(input_path=input_path, output_dir=output_dir, output_file=output_file)
    xz_file = lzma.open(absolute_data_path("analyses/filtered-exits-onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_equals(json_content["filters"]["tor/circuits"][0]["name"], "exclude_fingerprints")
    measurements = json_content['data']['op-hk6a']['tor']['circuits'][circuit_id]
    assert_false(measurements['filtered_out'])
    exit_measurements = json_content['data']['op-hk6a']['tor']['circuits'][exit_circuit_id]
    assert_true(exit_measurements['filtered_out'])
    onion_measurements = json_content['data']['op-hk6a']['tor']['circuits'][onion_circuit_id]
    assert_false(onion_measurements['filtered_out'])
