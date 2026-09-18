from app.tools.sql_query import sql_query_tool
from app.tools.analytics import analytics_tool
from app.tools.document_search import document_search_tool
from app.tools.data_comparison import data_comparison_tool
from app.tools.report_generator import report_generator_tool

ALL_TOOLS = [
    sql_query_tool,
    analytics_tool,
    document_search_tool,
    data_comparison_tool,
    report_generator_tool,
]
