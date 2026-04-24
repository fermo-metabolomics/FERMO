"""Manages dashboard data loading

Copyright (c) 2022-present Mitja Maximilian Zdouc, PhD & Hannah Esther Augustijn, MSc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import Self

from pydantic import BaseModel


class DashboardManager(BaseModel):
    """Organizes data extraction and filtering for dashboard

    Attributes:
        stats_analysis: static stats data from general analysis run
        stats_samples_dyn: mixed static and dynamic data on samples (overview)
        stats_chromatogram: all feature information structured per sample. Used for all dashboard visualizations
        stats_network: network information ordered by network ID
        stats_groups: overview of group labels to be used for filter selection
    """

    stats_analysis: dict = {}
    stats_samples_dyn: list = []
    stats_chromatogram: dict = {}
    stats_network: dict = {}
    stats_groups: dict = {}
    stats_fgroups: dict = {}
    stats_distplots: dict = {
        "novelty": [],
        "match": [],
        "phenotype": [],
    }

    def prepare_data_get(self: Self, f_sess: dict):
        """Run methods to prepare the data required by GET method

        Arguments:
            f_sess: fermo session file
        """
        self.extract_stats_analysis(f_sess)
        self.extract_stats_samples_dyn(f_sess)
        self.extract_network(f_sess)
        self.create_chromatogram(f_sess)
        self.collect_distplot(f_sess)

    def provide_data_get(self: Self) -> dict:
        """Return data required by GET method

        Returns: a json-compatible dict
        """
        return {
            "stats_analysis": self.stats_analysis,
            "stats_samples_dyn": self.stats_samples_dyn,
            "stats_chromatogram": self.stats_chromatogram,
            "stats_network": self.stats_network,
            "stats_groups": self.stats_groups,
            "stats_fgroups": self.stats_fgroups,
            "stats_distplots": self.stats_distplots,
        }

    def extract_stats_analysis(self: Self, f_sess: dict):
        """Extracts static analysis stats from fermo.session file

        Arguments:
            f_sess: fermo session file
        """
        try:
            self.stats_analysis = {
                "Total Samples": len(f_sess.get("stats", {}).get("samples")),
                "Molecular Features": f_sess.get("stats", {}).get("features"),
                "Removed Mol. Features": len(
                    f_sess.get("stats", {}).get("inactive_features")
                ),
                "FERMO-CORE Version": f_sess.get("metadata", {}).get(
                    "fermo_core_version"
                ),
                "Run date (YYYY-MM-DD)": (
                    f_sess.get("metadata", {}).get("file_created_isoformat")
                ).split("T")[0],
            }
        except TypeError:
            self.stats_analysis = {"error": "error during parsing of session file"}

    def extract_stats_samples_dyn(self: Self, f_sess: dict):
        """Extracts dynamic stats of samples

        Arguments:
            f_sess: fermo session file
        """
        try:
            groups = f_sess.get("stats", {}).get("groups", {}).get("categories", {})

            # TODO: handle no input metadata
            if groups == "":
                groups = "N/A"

            group_list = []
            sample_to_group = {}

            for group_id, categories in groups.items():
                group_list.append(group_id.title())
                for category, details in categories.items():
                    # to be used for group filtering sample -> category
                    if group_id in self.stats_groups:
                        self.stats_groups[group_id].append(category)
                    else:
                        self.stats_groups[group_id] = [category]
                    # to be used for group filtering feature -> category
                    for f_id in details["f_ids"]:
                        if f_id in self.stats_fgroups:
                            self.stats_fgroups[f_id].append(category)
                        else:
                            self.stats_fgroups[f_id] = [category]

                    for s_id in details["s_ids"]:
                        if s_id in sample_to_group:
                            sample_to_group[s_id].update({group_id.title(): category})
                        else:
                            sample_to_group[s_id] = {group_id.title(): category}

            for sample in f_sess.get("stats", {}).get("samples"):
                total_features = len(
                    f_sess.get("samples", {}).get(sample, {}).get("feature_ids")
                )
                remaining_features = total_features

                diversity = (
                    f_sess.get("samples", {})
                    .get(sample, {})
                    .get("scores", {})
                    .get("diversity")
                )
                specificity = (
                    f_sess.get("samples", {})
                    .get(sample, {})
                    .get("scores", {})
                    .get("specificity")
                )
                mean_novelty = (
                    f_sess.get("samples", {})
                    .get(sample, {})
                    .get("scores", {})
                    .get("mean_novelty")
                )

                group_info = sample_to_group.get(sample, {})
                if len(group_info.keys()) != len(group_list):
                    for item in group_list:
                        if item not in group_info:
                            group_info[item] = "N/A"
                ordered_group_info = {
                    key: group_info.get(key, "N/A") for key in group_list
                }

                self.stats_samples_dyn.append(
                    {
                        "Sample name": sample,
                        "Total features": total_features,
                        "Retained features": remaining_features,
                        "Diversity": diversity,
                        "Specificity": specificity,
                        "Mean novelty": mean_novelty,
                        **ordered_group_info,
                    }
                )
        except (TypeError, ValueError):
            self.stats_samples_dyn = {"error": "error during parsing of session file"}

    def create_chromatogram(self: Self, f_sess: dict):
        """Creates chromatogram from fermo.session file

        Arguments:
            f_sess: fermo session file
        """
        try:
            samples = f_sess.get("stats", {}).get("samples") or []
            for sample in samples:
                sample_data = f_sess.get("samples", {}).get(sample, {})
                feature_data = []
                for f_id in sample_data.get("feature_ids", []):
                    f_info = sample_data.get("sample_spec_features", {}).get(
                        str(f_id), {}
                    )
                    g_info = f_sess.get("general_features", {}).get(str(f_id), {})
                    novelty = g_info.get("scores", {}).get("novelty", {})
                    n_id_cosine = (
                        g_info.get("networks", {})
                        .get("modified_cosine", {})
                        .get("network_id", {})
                    )
                    n_id_deepscore = (
                        g_info.get("networks", {})
                        .get("ms2deepscore", {})
                        .get("network_id", {})
                    )

                    n_features_cosine = (
                        f_sess.get("stats", {})
                        .get("networks", {})
                        .get("modified_cosine", {})
                        .get("summary", {})
                        .get(str(n_id_cosine), {})
                    )
                    n_features_deepscore = (
                        f_sess.get("stats", {})
                        .get("networks", {})
                        .get("ms2deepscore", {})
                        .get("summary", {})
                        .get(str(n_id_deepscore), {})
                    )
                    if len(n_features_deepscore) >= 50:
                        n_features_deepscore = {}
                    if len(n_features_cosine) >= 50:
                        n_features_cosine = {}

                    feature_data.append(
                        {
                            "f_id": f_info.get("f_id"),
                            "rt": f_info.get("rt"),
                            "rt_avg": g_info.get("rt"),
                            "trace_rt": f_info.get("trace_rt"),
                            "trace_int": f_info.get("trace_int"),
                            "abs_int": f_info.get("intensity"),
                            "rel_int": f_info.get("rel_intensity"),
                            "blank": g_info.get("blank"),
                            "novelty": novelty if novelty else 0,
                            "mz": g_info.get("mz"),
                            "samples": g_info.get("samples"),
                            "f_group": g_info.get("group_factors"),
                            "f_sample": g_info.get("height_per_sample"),
                            "a_sample": g_info.get("area_per_sample"),
                            "annotations": g_info.get("annotations"),
                            "n_cos_id": n_id_cosine,
                            "n_ms2d_id": n_id_deepscore,
                            "n_features_cosine": n_features_cosine,
                            "n_features_deepscore": n_features_deepscore,
                        }
                    )
                self.stats_chromatogram[sample] = feature_data

        except TypeError:
            self.stats_chromatogram = {"error": "error during parsing of session file"}

    def extract_network(self: Self, f_sess: dict):
        """Extracts network data from fermo.session file

        Arguments:
            f_sess: fermo session file
        """
        try:
            networks = f_sess.get("stats", {}).get("networks") or []

            for network in networks:
                n_info = networks.get(network, {})
                network_data = {}
                for n_id in n_info.get("subnetworks", {}):
                    network_size = len(
                        n_info.get("subnetworks", {})
                        .get(n_id)
                        .get("elements", {})
                        .get("nodes", {})
                    )
                    if network_size >= 50:
                        network_data[n_id] = "large_network"
                    else:
                        network_data[n_id] = n_info.get("subnetworks", {}).get(n_id)

                self.stats_network[network] = network_data

        except TypeError:
            self.stats_network = {"error": "error during parsing of session file"}

    def collect_distplot(self: Self, f_sess: dict):
        """Parse values for distribution plots"""
        try:
            features = f_sess.get("general_features", {})
            for _k, v in features.items():
                if v.get("scores"):
                    self.stats_distplots["novelty"].append(
                        v["scores"].get("novelty", 0.0)
                    )
                    self.stats_distplots["phenotype"].append(
                        v["scores"].get("phenotype", 0.0)
                    )

                if matches := v.get("annotations", {}).get("matches"):
                    for m in matches:
                        self.stats_distplots["match"].append(m.get("score", 0.0))
                else:
                    self.stats_distplots["match"].append(0.0)

        except TypeError:
            self.stats_distplots = {"error": "error during parsing of session file"}
