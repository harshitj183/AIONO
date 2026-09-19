"""
Unit tests for all 5 agent tools.
Tests real database queries against seeded data.

Run: pytest tests/test_tools.py -v
"""

import json
import pytest


# ── sql_query_tool ────────────────────────────────────────────

class TestSqlQueryTool:
    def test_valid_select_returns_data(self):
        from app.tools.sql_query import sql_query_tool
        result = sql_query_tool.invoke({"query": "SELECT COUNT(*) as total FROM support_tickets"})
        data = json.loads(result)
        assert "error" not in data
        assert data["rows"][0]["total"] > 0

    def test_blocks_write_operations(self):
        from app.tools.sql_query import sql_query_tool
        result = sql_query_tool.invoke({"query": "DELETE FROM users WHERE 1=1"})
        data = json.loads(result)
        assert "error" in data
        assert "SELECT" in data["error"] or "permitted" in data["error"]

    def test_blocks_disallowed_table(self):
        from app.tools.sql_query import sql_query_tool
        result = sql_query_tool.invoke({"query": "SELECT * FROM sqlite_master"})
        data = json.loads(result)
        assert "error" in data

    def test_caps_rows_at_25(self):
        from app.tools.sql_query import sql_query_tool
        result = sql_query_tool.invoke({"query": "SELECT * FROM sales"})
        data = json.loads(result)
        assert data["row_count"] <= 25

    def test_returns_columns_list(self):
        from app.tools.sql_query import sql_query_tool
        result = sql_query_tool.invoke({"query": "SELECT id, product_name, amount FROM sales LIMIT 5"})
        data = json.loads(result)
        assert "columns" in data
        assert set(data["columns"]) == {"id", "product_name", "amount"}


# ── analytics_tool ────────────────────────────────────────────

class TestAnalyticsTool:
    def test_complaint_spike_analysis(self):
        from app.tools.analytics import analytics_tool
        result = analytics_tool.invoke({"metric": "complaint_spike_analysis", "period_days": 30})
        data = json.loads(result)
        assert "error" not in data
        assert "data" in data
        assert len(data["data"]) > 0
        # Each item has required keys
        item = data["data"][0]
        assert "category" in item
        assert "recent_count" in item
        assert "change_pct" in item

    def test_ticket_volume_trend(self):
        from app.tools.analytics import analytics_tool
        result = analytics_tool.invoke({"metric": "ticket_volume_trend", "period_days": 30})
        data = json.loads(result)
        assert "error" not in data
        assert isinstance(data["data"], list)

    def test_employee_attrition_summary(self):
        from app.tools.analytics import analytics_tool
        result = analytics_tool.invoke({"metric": "employee_attrition_summary"})
        data = json.loads(result)
        assert "error" not in data
        assert len(data["data"]) > 0
        assert "department" in data["data"][0]

    def test_unknown_metric_returns_error(self):
        from app.tools.analytics import analytics_tool
        result = analytics_tool.invoke({"metric": "nonexistent_metric"})
        data = json.loads(result)
        assert "error" in data

    def test_product_revenue_summary(self):
        from app.tools.analytics import analytics_tool
        result = analytics_tool.invoke({"metric": "product_revenue_summary", "period_days": 90})
        data = json.loads(result)
        assert "error" not in data
        assert len(data["data"]) > 0


# ── document_search_tool ──────────────────────────────────────

class TestDocumentSearchTool:
    def test_keyword_search_returns_results(self):
        from app.tools.document_search import document_search_tool
        result = document_search_tool.invoke({"query": "authentication login AIONO Investigator", "top_k": 3})
        data = json.loads(result)
        assert "error" not in data
        assert "results" in data
        assert len(data["results"]) > 0

    def test_result_has_required_fields(self):
        from app.tools.document_search import document_search_tool
        result = document_search_tool.invoke({"query": "attrition HR employees", "top_k": 2})
        data = json.loads(result)
        for doc in data["results"]:
            assert "title" in doc
            assert "snippet" in doc
            assert "doc_type" in doc
            assert "source" in doc or "author" in doc

    def test_top_k_respected(self):
        from app.tools.document_search import document_search_tool
        result = document_search_tool.invoke({"query": "report", "top_k": 2})
        data = json.loads(result)
        assert len(data["results"]) <= 2

    def test_empty_db_graceful(self):
        # Tool should not crash on bad query
        from app.tools.document_search import document_search_tool
        result = document_search_tool.invoke({"query": "xyzzy_no_match_expected_12345", "top_k": 3})
        data = json.loads(result)
        # Either empty results or error — must not throw
        assert "results" in data or "error" in data


# ── data_comparison_tool ──────────────────────────────────────

class TestDataComparisonTool:
    def test_month_over_month_tickets(self):
        from app.tools.data_comparison import data_comparison_tool
        result = data_comparison_tool.invoke({"compare_type": "month_over_month_tickets", "period_days": 30})
        data = json.loads(result)
        assert "error" not in data
        assert "summary" in data
        assert "current_total" in data["summary"]
        assert "total_change_pct" in data["summary"]

    def test_month_over_month_revenue(self):
        from app.tools.data_comparison import data_comparison_tool
        result = data_comparison_tool.invoke({"compare_type": "month_over_month_revenue", "period_days": 30})
        data = json.loads(result)
        assert "error" not in data
        assert "revenue_change_pct" in data
        assert "significance" in data

    def test_severity_trend(self):
        from app.tools.data_comparison import data_comparison_tool
        result = data_comparison_tool.invoke({"compare_type": "severity_trend_comparison", "period_days": 30})
        data = json.loads(result)
        assert "breakdown" in data
        severities = {item["severity"] for item in data["breakdown"]}
        assert "high" in severities or "critical" in severities

    def test_product_comparison_requires_both_products(self):
        from app.tools.data_comparison import data_comparison_tool
        result = data_comparison_tool.invoke({"compare_type": "product_ticket_comparison"})
        data = json.loads(result)
        assert "error" in data

    def test_unknown_compare_type(self):
        from app.tools.data_comparison import data_comparison_tool
        result = data_comparison_tool.invoke({"compare_type": "unknown_type"})
        data = json.loads(result)
        assert "error" in data


# ── report_generator_tool ─────────────────────────────────────

class TestReportGeneratorTool:
    def _make_report(self, **kwargs):
        from app.tools.report_generator import report_generator_tool
        defaults = {
            "question": "Why did complaints increase?",
            "root_cause": "Authentication regression in AIONO Investigator v2.3.0",
            "evidence": [
                {"claim": "Login tickets up 78%", "source": "analytics_tool", "data": "78%", "confidence": "high"},
                {"claim": "Incident report confirms OAuth regression", "source": "documents", "data": "INC-2024-089", "confidence": "high"},
            ],
            "recommendations": ["Deploy hotfix", "Add monitoring", "Update triage guide"],
            "confidence": "high",
            "needs_human_review": False,
        }
        defaults.update(kwargs)
        return json.loads(report_generator_tool.invoke(defaults))

    def test_complete_report_structure(self):
        report = self._make_report()
        assert report["root_cause"] != ""
        assert report["confidence"] == "high"
        assert report["evidence_count"] == 2
        assert len(report["recommendations"]) == 3
        assert report["needs_human_review"] is False
        assert report["report_status"] == "complete"

    def test_evidence_quality_strong(self):
        # 3+ items with high confidence → strong
        report = self._make_report(evidence=[
            {"claim": "Login tickets up 78%", "source": "analytics_tool", "data": "78%", "confidence": "high"},
            {"claim": "Incident report confirms OAuth regression", "source": "documents", "data": "INC-2024-089", "confidence": "high"},
            {"claim": "Spike analysis shows 34% increase", "source": "data_comparison_tool", "data": "34%", "confidence": "high"},
        ])
        assert report["evidence_quality"] == "strong"

    def test_evidence_quality_moderate(self):
        # 2 items → moderate
        report = self._make_report()
        assert report["evidence_quality"] == "moderate"

    def test_empty_evidence_returns_error(self):
        from app.tools.report_generator import report_generator_tool
        result = json.loads(report_generator_tool.invoke({
            "question": "Test", "root_cause": "Test cause",
            "evidence": [], "recommendations": [], "confidence": "low",
        }))
        assert "error" in result

    def test_empty_root_cause_returns_error(self):
        from app.tools.report_generator import report_generator_tool
        result = json.loads(report_generator_tool.invoke({
            "question": "Test", "root_cause": "",
            "evidence": [{"claim": "c", "source": "s", "data": "d", "confidence": "high"}],
            "recommendations": [], "confidence": "low",
        }))
        assert "error" in result

    def test_needs_review_sets_status(self):
        report = self._make_report(needs_human_review=True)
        assert report["report_status"] == "needs_review"
