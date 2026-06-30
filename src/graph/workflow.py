from langgraph.graph import StateGraph, START, END
from .state import VideoAuditState
from .nodes import (
    index_video_node,
    retrieval_node,
    compliance_auditor_node,
    report_node,
)

# Initialize the state graph with our defined state schema
workflow = StateGraph(VideoAuditState)

# Add all processing nodes
workflow.add_node("index_video", index_video_node)
workflow.add_node("retrieve", retrieval_node)
workflow.add_node("audit", compliance_auditor_node)
workflow.add_node("report", report_node)

# Set the linear execution flow
workflow.add_edge(START, "index_video")
workflow.add_edge("index_video", "retrieve")
workflow.add_edge("retrieve", "audit")
workflow.add_edge("audit", "report")
workflow.add_edge("report", END)

# Compile the graph into an executable Runnable
app = workflow.compile()
