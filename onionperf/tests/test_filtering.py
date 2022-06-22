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
    input_path = absolute_data_path("analyses/onionperf.analysis.json.xz")
    output_dir = absolute_data_path("analyses/")
    output_file = "filtered-onionperf.analysis.json.xz"
    filtering.apply_filters(input_path=input_path, output_dir=output_dir, output_file=output_file)
    xz_file = lzma.open(absolute_data_path("analyses/filtered-onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_equals(json_content["filters"], json.loads('{"tor/circuits": [{"name": "exclude_cbt"}]}'))
    circuit_id = "23"
    measurements = json_content['data']['groot']['tor']['circuits'][circuit_id]
    assert_false(measurements['cbt_set'])
    assert_true(measurements['filtered_out'])

def test_exclude_fingerprints():
    filtering = Filtering()
    fingerprint = "3CE90527D5712296B58E7EB7CD57F7D388D25FBB"
    filtering.fingerprints_to_exclude = []
    filtering.fingerprints_to_exclude.append(fingerprint)
    filtering.fingerprints_to_exclude_path = absolute_data_path("analyses/fingerprints.txt")
    input_path = absolute_data_path("analyses/onionperf.analysis.json.xz")
    output_dir = absolute_data_path("analyses/")
    output_file = "filtered-fp-onionperf.analysis.json.xz"
    filtering.apply_filters(input_path=input_path, output_dir=output_dir, output_file=output_file)
    xz_file = lzma.open(absolute_data_path("analyses/filtered-fp-onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_equals(json_content["filters"]["tor/circuits"][0]["name"], "exclude_fingerprints")
    circuit_id = "23"
    measurements = json_content['data']['groot']['tor']['circuits'][circuit_id]
    assert_true(measurements['filtered_out'])

def test_exclude_guards():
    guard = "A7A9F4B9D4157F0F4AB96AF83F3F188B7E685539"
    guard_circuit_id = "25"
    fingerprint = "7185B69E3267E71D0E4CBE30209677205DEA5E67"
    circuit_id = "26"
    filtering = Filtering()
    filtering.guards = True
    filtering.fingerprints_to_exclude = []
    filtering.fingerprints_to_exclude.append(guard)
    filtering.fingerprints_to_exclude.append(fingerprint)
    filtering.fingerprints_to_exclude_path = absolute_data_path("analyses/guards-fingerprints.txt")
    input_path = absolute_data_path("analyses/onionperf.analysis.json.xz")
    output_dir = absolute_data_path("analyses/")
    output_file = "filtered-guards-onionperf.analysis.json.xz"
    filtering.apply_filters(input_path=input_path, output_dir=output_dir, output_file=output_file)
    xz_file = lzma.open(absolute_data_path("analyses/filtered-guards-onionperf.analysis.json.xz"))
    json_content = json.load(xz_file)
    assert_equals(json_content["filters"]["tor/circuits"][0]["name"], "exclude_fingerprints")
    measurements = json_content['data']['groot']['tor']['circuits'][circuit_id]
    assert_false(measurements['filtered_out'])
    guard_measurements = json_content['data']['groot']['tor']['circuits'][guard_circuit_id]
    assert_true(guard_measurements['filtered_out'])
