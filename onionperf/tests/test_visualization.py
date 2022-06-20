
from nose.tools import *
import pkg_resources
from pandas import Timestamp
from onionperf.analysis import OPAnalysis
from onionperf.visualization import TGenVisualization

def absolute_data_path(relative_path=""):
    """
    Returns an absolute path for test data given a relative path.
    """
    return pkg_resources.resource_filename("onionperf",
                                           "tests/data/" + relative_path)


DATA_DIR = absolute_data_path()

def test_create_data_frame_v3():
    path = DATA_DIR + "analyses/"
    filename = "2021-01-01.op-hk5.onionperf.analysis.json.xz"

    known_ttfbs = [4.134508, 1.129437, 11.376374, 4.29965, 1.49145]
    known_ttlbs = [34.725328, 11.817973, 18.613478, 26.635889, 11.187625]

    known_filesize_bytes = [5242880]
    known_starts = [Timestamp('2021-01-01 00:01:49.410935'),
                    Timestamp('2021-01-01 00:06:49.411600'),
                    Timestamp('2021-01-01 00:11:49.412198'),
                    Timestamp('2021-01-01 00:16:49.412745'),
                    Timestamp('2021-01-01 00:21:49.413580')]
    known_throughput = [1.2165419733844904,
                        3.539323813686757,
                        5.579639119028994,
                        1.8477830523348604,
                        3.9898140599836576]
    known_total_onion_dls = 2
    known_total_public_dls = 3

    tgen_viz = TGenVisualization()
    analyses = []
    analysis = OPAnalysis.load(filename=filename, input_prefix=path)
    analyses.append(analysis)
    tgen_viz.add_dataset(analyses, "test")
    tgen_viz._TGenVisualization__extract_data_frame(onion=False, public=False)


    onion_downloads = tgen_viz.data[(tgen_viz.data["server"] == 'onion')]
    public_downloads = tgen_viz.data[(tgen_viz.data["server"] == 'public')]
    exist_errors = tgen_viz.data["error_code"].count() > 0

    assert_equals(sorted(tgen_viz.data["time_to_first_byte"].to_list()), sorted(known_ttfbs))
    assert_equals(sorted(tgen_viz.data["time_to_last_byte"].to_list()), sorted(known_ttlbs))
    assert_equals(tgen_viz.data["filesize_bytes"].unique().tolist(), known_filesize_bytes)
    assert_equals(sorted(tgen_viz.data["start"].tolist()), sorted(known_starts))
    assert_equals(sorted(tgen_viz.data["mbps"].tolist()), sorted(known_throughput))
    assert_equals(len(onion_downloads), known_total_onion_dls)
    assert_equals(len(public_downloads), known_total_public_dls)
    assert_equals(exist_errors, False)


def test_create_data_frame_v3p1_filters():
    path = DATA_DIR + "analyses/"
    filename = "2021-06-01.op-hk6a.onionperf.analysis.json.xz"

    known_ttfbs = [0.926961, 1.056154, 7.770001]
    known_ttlbs = [10.061804, 10.787324, 286.022849]

    known_filesize_bytes = [5242880]
    known_starts = [Timestamp('2021-06-01 00:01:38.434906'),
                    Timestamp('2021-06-01 01:29:46.278690'),
                    Timestamp('2021-06-01 23:59:21.837000')]
    known_throughput = [4.638636689133778,  4.365865032309641]
    known_total_onion_dls = 1
    known_total_public_dls = 2
    total_errors = 1
    known_guards = ['0C8CDE060281DDA38F69F1765049D16D9DE9320E',
                    'A96DA63E4415E776FBFCCF3DA7154C804534B6E7',
                    'ECF1060A8597A846C0C705A1AE260EADEE93B50D']

    tgen_viz = TGenVisualization()
    analyses = []
    analysis = OPAnalysis.load(filename=filename, input_prefix=path)
    analyses.append(analysis)
    tgen_viz.add_dataset(analyses, "test")
    tgen_viz._TGenVisualization__extract_data_frame(onion=False, public=False)


    onion_downloads = tgen_viz.data[(tgen_viz.data["server"] == 'onion')]
    public_downloads = tgen_viz.data[(tgen_viz.data["server"] == 'public')]

    assert_equals(sorted(tgen_viz.data["time_to_first_byte"].to_list()), sorted(known_ttfbs))
    assert_equals(sorted(tgen_viz.data["time_to_last_byte"].to_list()), sorted(known_ttlbs))
    assert_equals(tgen_viz.data["filesize_bytes"].unique().tolist(), known_filesize_bytes)
    assert_equals(sorted(tgen_viz.data["start"].tolist()), sorted(known_starts))
    assert_equals(sorted(tgen_viz.data["mbps"].dropna().tolist()), sorted(known_throughput))
    assert_equals(len(onion_downloads), known_total_onion_dls)
    assert_equals(len(public_downloads), known_total_public_dls)
    assert_equals(tgen_viz.data["error_code"].count() > 0, True)
    assert_equals(len(tgen_viz.data["error_code"].dropna()), total_errors)
    assert_equals(sorted(tgen_viz.data["guard"].to_list()), sorted(known_guards))


def test_create_data_frame_v3p1_no_filters():
    path = DATA_DIR + "analyses/"
    filename = "2021-06-01.op-hk6a.onionperf.analysis_no_filters.json.xz"
    known_ttfbs = [0.926961, 1.056154, 1.083673, 1.098328, 1.191881, 7.770001]
    known_ttlbs = [9.095904, 10.061804, 10.787324, 10.992984, 20.517444, 286.022849]

    known_filesize_bytes = [5242880]
    known_starts = [Timestamp('2021-06-01 00:01:38.434906'),
                    Timestamp('2021-06-01 01:29:46.278690'),
                    Timestamp('2021-06-01 23:59:21.837000'),
                    Timestamp('2021-06-01 00:00:08.432599'),
                    Timestamp('2021-06-01 00:00:38.433598'),
                    Timestamp('2021-06-01 00:01:08.434188'),
                    ]
    known_throughput = [2.175934990223527,
                        4.2963751322033215,
                        4.638636689133778,
                        4.365865032309641,
                        5.927724874006106]
    known_total_onion_dls = 1
    known_total_public_dls = 5
    known_guards = ['0C8CDE060281DDA38F69F1765049D16D9DE9320E',
                    'A96DA63E4415E776FBFCCF3DA7154C804534B6E7',
                    'ECF1060A8597A846C0C705A1AE260EADEE93B50D',
                    'A96DA63E4415E776FBFCCF3DA7154C804534B6E7']

    tgen_viz = TGenVisualization()
    analyses = []
    analysis = OPAnalysis.load(filename=filename, input_prefix=path)
    analyses.append(analysis)
    tgen_viz.add_dataset(analyses, "test")
    tgen_viz._TGenVisualization__extract_data_frame(onion=False, public=False)

    onion_downloads = tgen_viz.data[(tgen_viz.data["server"] == 'onion')]
    public_downloads = tgen_viz.data[(tgen_viz.data["server"] == 'public')]
    assert_equals(sorted(tgen_viz.data["time_to_first_byte"].to_list()), sorted(known_ttfbs))
    assert_equals(sorted(tgen_viz.data["time_to_last_byte"].to_list()), sorted(known_ttlbs))
    assert_equals(tgen_viz.data["filesize_bytes"].unique().tolist(), known_filesize_bytes)
    assert_equals(sorted(tgen_viz.data["start"].tolist()), sorted(known_starts))
    assert_equals(sorted(tgen_viz.data["mbps"].dropna().tolist()), sorted(known_throughput))
    assert_equals(len(onion_downloads), known_total_onion_dls)
    assert_equals(len(public_downloads), known_total_public_dls)
    assert_equals(sorted(tgen_viz.data["guard"].dropna().to_list()), sorted(known_guards))

def test_exclude_cbt_option():
    path = DATA_DIR + "analyses/"
    filename = "2021-06-01.op-hk6a.onionperf.analysis.json.xz"

    tgen_viz = TGenVisualization()
    analyses = []
    analysis = OPAnalysis.load(filename=filename, input_prefix=path)
    analyses.append(analysis)
    tgen_viz.add_dataset(analyses, "test")
    tgen_viz._TGenVisualization__extract_data_frame(onion=False, public=False)
    circuit_id = "181935"
    measurements = analysis.json_db['data']['op-hk6a']['tor']['circuits'][circuit_id]
    assert_false(measurements['cbt_set'])
    assert_true(measurements['filtered_out'])
    fingerprints = []
    for guard in measurements['current_guards']:
        fg = "${}~{}".format(guard['fingerprint'], guard['nickname'])
        fingerprints.append(fg)
    check = False
    control = ['$0C8CDE060281DDA38F69F1765049D16D9DE9320E~vulgarismagistralis',
               '$A96DA63E4415E776FBFCCF3DA7154C804534B6E7~3735928559',
               '$248A96B2A88A3EAB14699B9096CE6ABF77D0606A~Illuminati']

    check_ctl = False
    for fs in tgen_viz.data["fingerprints"]:
        if fs == fingerprints:
            check = True
        if fs == control:
            check_ctl = True
    assert_false(check)
    assert_true(check_ctl)
