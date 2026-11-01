"""
TC-TLS-003 (REQ-TLS-003): scholarly records through the door (tool_calls.py): one record format with origin (sources), trust class and retraction
state, a strict date cut-off with reason codes, retracted works dropped and listed. The real scholar.Scholar and trust table run; the five APIs are fakes.
Run with: python tests/test_tool_calls_scholar.py
"""

import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                   # noqa: E402
from scholar import Scholar, latest_day, new_work          # noqa: E402
from source_trust import TrustTable                        # noqa: E402
from tool_calls import ToolCalls, ToolCallError            # noqa: E402
from web_tools import WebError                             # noqa: E402

RUN = {"id": "r1", "limits": {}}
CUTOFF = "2001-11-22"
RETRACTED = {"status": "retracted", "notices": [{"type": "retracted", "date": "2001-06-01", "doi": "10.9/notice"}], "hints": []}
LATER = {"status": "retracted", "notices": [{"type": "retracted", "date": "2005-01-01", "doi": "10.9/later"}], "hints": []}


class FakeClient:
    """one scholarly API: fresh records on every search, or a WebError"""

    def __init__(self, name, records=(), error=None):
        self.name, self.records, self.error = name, list(records), error

    def search(self, query, limit=10, until=None, since=None):
        if self.error:
            raise WebError(self.error)
        return [new_work(self.name, **dict(fields)) for fields in self.records]


def door(*clients, retractions=None):
    return ToolCalls(scholar=Scholar(list(clients)), work_trust=TrustTable.load().for_work, retractions=retractions)


def dated(*dates):
    return [{"doi": "10.1/%d" % i, "title": "Work %d" % i, "date": date} for i, date in enumerate(dates)]


class ScholarlyRecordTests(unittest.TestCase):

    @mark.req("REQ-TLS-003")
    def test_the_cut_off_is_strict_and_names_its_reason(self):
        """TC-TLS-003: the cut-off is strict and names its reason.

        Example: door(FakeClient("openalex", dated("2001-11-22", "2001-11", "2001", None))).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        """
        # Given: ...
        out = door(FakeClient("openalex", dated("2001-11-22", "2001-11", "2001", None))).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        # When: ...
        # Then: ...
        self.assertEqual([w["doi"] for w in out["works"]], ["10.1/0"])
        self.assertEqual(sorted((d["ref"], d["reason"]) for d in out["dropped"]), [("doi:10.1/1", "after_cutoff"), ("doi:10.1/2", "after_cutoff"), ("doi:10.1/3", "no_date")])

    @mark.req("REQ-TLS-003")
    def test_no_kept_work_violates_the_cut_off(self):
        """TC-TLS-003: no kept work violates the cut-off.

        Example: dates = ["1999", "2001", "2001-10", "2001-11", "2001-11-21", "2001-11-22", "2001-11-23", "2001-12-01", "2002-01-01", None]; door(FakeClient("crossref", dated(*dates))).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        """
        # Given: ...
        dates = ["1999", "2001", "2001-10", "2001-11", "2001-11-21", "2001-11-22", "2001-11-23", "2001-12-01", "2002-01-01", None]
        out = door(FakeClient("crossref", dated(*dates))).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        # When: ...
        # Then: ...
        self.assertEqual(len(out["works"]) + len(out["dropped"]), len(dates))
        self.assertTrue(all(str(latest_day(w["date"])) <= CUTOFF for w in out["works"]))
        self.assertEqual(sorted(w["date"] for w in out["works"]), ["1999", "2001-10", "2001-11-21", "2001-11-22"])

    @mark.req("REQ-TLS-003")
    def test_a_work_retracted_before_the_cut_off_is_dropped_and_listed(self):
        """TC-TLS-003: a work retracted before the cut-off is dropped and listed.

        Example: records = [{"doi": "10.1/ok", "title": "Fine", "date": "2000"}, {"doi": "10.1/bad", "title": "Retracted", "date": "2000", "retraction": RETRACTED}]; door(FakeClient("pubmed", records)).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        """
        # Given: ...
        records = [{"doi": "10.1/ok", "title": "Fine", "date": "2000"}, {"doi": "10.1/bad", "title": "Retracted", "date": "2000", "retraction": RETRACTED}]
        out = door(FakeClient("pubmed", records)).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        # When: ...
        # Then: ...
        self.assertEqual([w["doi"] for w in out["works"]], ["10.1/ok"])
        self.assertEqual([(d["ref"], d["reason"]) for d in out["dropped"]], [("doi:10.1/bad", "retracted")])

    @mark.req("REQ-TLS-003")
    def test_a_retraction_after_the_cut_off_does_not_steer_the_run(self):
        """TC-TLS-003: a retraction after the cut-off does not steer the run.

        Example: records = [{"doi": "10.1/late", "title": "Retracted later", "date": "2000", "retraction": LATER}]; door(FakeClient("pubmed", records)).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        """
        # Given: ...
        records = [{"doi": "10.1/late", "title": "Retracted later", "date": "2000", "retraction": LATER}]
        out = door(FakeClient("pubmed", records)).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        # When: ...
        # Then: ...
        self.assertEqual([w["doi"] for w in out["works"]], ["10.1/late"])
        self.assertEqual(out["dropped"], [])

    @mark.req("REQ-TLS-003")
    def test_the_retraction_check_is_asked_for_every_kept_work(self):
        """TC-TLS-003: the retraction check is asked for every kept work.

        Example: asked = []; def retractions(work, errors): asked.append(work["doi"]); if work["doi"] == "10.1/1": work["retraction"] = RETRACTED; return work; door(FakeClient("openalex", dated("2000", "2000")), retractions=retractions).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        """
        # Given: ...
        asked = []
        def retractions(work, errors):
            asked.append(work["doi"])
            if work["doi"] == "10.1/1":
                work["retraction"] = RETRACTED
            return work
        out = door(FakeClient("openalex", dated("2000", "2000")), retractions=retractions).call(RUN, "scholar_search", {"query": "q", "until": CUTOFF})["output"]
        # When: ...
        # Then: ...
        self.assertEqual(asked, ["10.1/0", "10.1/1"])
        self.assertEqual([(d["ref"], d["reason"]) for d in out["dropped"]], [("doi:10.1/1", "retracted")])

    @mark.req("REQ-TLS-003")
    def test_every_record_has_origin_trust_class_and_retraction_state(self):
        """TC-TLS-003: every record has origin trust class and retraction state.

        Example: door(FakeClient("openalex", dated("2000")), FakeClient("pubmed", error="rate limited")).call(RUN, "scholar_search", {"query": "q", "until": None})
        """
        # Given: ...
        out = door(FakeClient("openalex", dated("2000")), FakeClient("pubmed", error="rate limited")).call(RUN, "scholar_search", {"query": "q", "until": None})
        work = out["output"]["works"][0]
        # When: ...
        # Then: ...
        self.assertEqual(out["trust"], "web")
        self.assertEqual(work["sources"], ["openalex"])
        self.assertIn("class", work["trust"])
        self.assertIn(work["retraction"]["status"], ("none", "unknown"))
        self.assertEqual(out["output"]["errors"], [{"source": "pubmed", "message": "rate limited"}])

    @mark.req("REQ-TLS-003")
    def test_a_source_record_of_a_doi_has_trust_class_and_retraction_state(self):
        """TC-TLS-003: source_record of a DOI asks the lookup for the work and gives its trust class and retraction state.

        Example: source_record "doi:10.1/bad" of a retracted work -> class from the trust table, retraction status "retracted".
        """
        # Given: a lookup that knows one retracted work
        works = {"10.1/bad": new_work("crossref", doi="10.1/bad", title="Retracted", date="2000", retraction=RETRACTED)}
        tools = ToolCalls(work_trust=TrustTable.load().for_work, work_lookup=works.get)
        # When: the record of its DOI is asked for
        out = tools.call(RUN, "source_record", {"ref": "doi:10.1/bad"})
        # Then: it has the reference, a trust class and score, the retraction state, and the web trust label
        self.assertEqual((out["trust"], out["output"]["ref"]), ("web", "doi:10.1/bad"))
        self.assertEqual(set(out["output"]), {"ref", "class", "trust", "retraction"})
        self.assertIsInstance(out["output"]["class"], str)
        self.assertEqual(out["output"]["retraction"]["status"], "retracted")

    @mark.req("REQ-TLS-003")
    def test_an_unknown_doi_is_a_source_error(self):
        """TC-TLS-003: a DOI the lookup does not know is a source error, not an empty record.

        Example: source_record "10.1/none" -> ToolCallError source_error.
        """
        # Given: a lookup that knows nothing
        tools = ToolCalls(work_trust=TrustTable.load().for_work, work_lookup=lambda doi: None)
        # When: a record is asked for
        with self.assertRaises(ToolCallError) as caught:
            tools.call(RUN, "source_record", {"ref": "10.1/none"})
        # Then: the call fails as a source error
        self.assertEqual(caught.exception.code, "source_error")


if __name__ == "__main__":
    unittest.main()
