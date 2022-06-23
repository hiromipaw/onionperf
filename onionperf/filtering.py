'''
  OnionPerf
  Authored by Rob Jansen, 2015
  Copyright 2015-2020 The Tor Project
  See LICENSE for licensing information
'''

import sys, re
import logging
from onionperf.analysis import OPAnalysis

class Filtering(object):

    def __init__(self):
        self.fingerprints_to_include = None
        self.fingerprints_to_exclude = None
        self.exclude_cbt = False
        self.guards = False
        self.exits = False
        self.fingerprint_pattern = re.compile("\$?([0-9a-fA-F]{40})")

    def include_fingerprints(self, path):
        self.fingerprints_to_include = []
        self.fingerprints_to_include_path = path
        with open(path, 'rt') as f:
            for line in f:
                fingerprint_match = self.fingerprint_pattern.match(line)
                if fingerprint_match:
                    fingerprint = fingerprint_match.group(1).upper()
                    self.fingerprints_to_include.append(fingerprint)

    def exclude_fingerprints(self, path):
        self.fingerprints_to_exclude = []
        self.fingerprints_to_exclude_path = path
        with open(path, 'rt') as f:
            for line in f:
                fingerprint_match = self.fingerprint_pattern.match(line)
                if fingerprint_match:
                    fingerprint = fingerprint_match.group(1).upper()
                    self.fingerprints_to_exclude.append(fingerprint)

    def filter_tor_circuits(self, analysis):

        if self.fingerprints_to_include is None and self.fingerprints_to_exclude is None and not self.exclude_cbt:
            return
        filters = analysis.json_db.setdefault("filters", {})
        tor_circuits_filters = filters.setdefault("tor/circuits", [])
        if self.fingerprints_to_include:
           tor_circuits_filters.append({"name": "include_fingerprints", "filepath": self.fingerprints_to_include_path })
        if self.fingerprints_to_exclude:
           tor_circuits_filters.append({"name": "exclude_fingerprints", "filepath": self.fingerprints_to_exclude_path })
        if self.exclude_cbt:
           if str(analysis.json_db["version"]) < '3.1':
               logging.error("Analysis is version {}, but version 3.1 or higher is required.".format(analysis.json_db["version"]))
               sys.exit(1)
           tor_circuits_filters.append({"name": "exclude_cbt"})
           for source in analysis.get_nodes():
               tor_circuits = analysis.get_tor_circuits(source)
               filtered_circuit_ids = []
               for circuit_id, tor_circuit in tor_circuits.items():
                   keep = False
                   if "cbt_set" in tor_circuit and tor_circuit["cbt_set"] == True:
                       keep = True
                   if not keep:
                       tor_circuits[circuit_id]["filtered_out"] = True
                   else:
                       tor_circuits[circuit_id]["filtered_out"] = False
                   tor_circuits[circuit_id] = dict(sorted(tor_circuit.items()))

        for source in analysis.get_nodes():
            tor_circuits = analysis.get_tor_circuits(source)
            filtered_circuit_ids = []
            for circuit_id, tor_circuit in tor_circuits.items():
                keep = False
                if "path" in tor_circuit:
                    path = tor_circuit["path"]
                    keep = True
                    if self.guards:
                        long_name, _ = path[0]
                        keep = self.__fingerprint_path_match(long_name)
                    elif self.exits:
                        streams = analysis.get_tor_streams(source)
                        s = list(filter(lambda x:x["circuit_id"] == circuit_id, streams.values()))
                        if s:
                            s = s.pop()
                            if not ".onion:" in s["target"]:
                                long_name, _ = path[-1]
                                keep = self.__fingerprint_path_match(long_name)
                    else:
                        for long_name, _ in path:
                            keep = self.__fingerprint_path_match(long_name)
                            if not keep:
                                break

                if not keep:
                    tor_circuits[circuit_id]["filtered_out"] = True
                    tor_circuits[circuit_id] = dict(sorted(tor_circuit.items()))

    def __fingerprint_path_match(self, long_name):
        keep = True
        fingerprint_match = self.fingerprint_pattern.match(long_name)
        if fingerprint_match:
            fingerprint = fingerprint_match.group(1).upper()
            if self.fingerprints_to_include is not None and fingerprint not in self.fingerprints_to_include:
                keep = False
            if self.fingerprints_to_exclude is not None and fingerprint in self.fingerprints_to_exclude:
                keep = False
        return keep

    def apply_filters(self, input_path, output_dir, output_file):
        analysis = OPAnalysis.load(filename=input_path)
        self.filter_tor_circuits(analysis)
        analysis.json_db["version"] = '3.1'
        analysis.json_db = dict(sorted(analysis.json_db.items()))
        analysis.save(filename=output_file, output_prefix=output_dir, sort_keys=False)
