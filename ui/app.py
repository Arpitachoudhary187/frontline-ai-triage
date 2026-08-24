"""Premium Streamlit UI for FRONTLINE triage classifier."""

import streamlit as st
import pandas as pd
import json
import logging
from pathlib import Path
from datetime import datetime
from src.triage import TriagePipeline
from src.dataset import DatasetAdapter
from src.evaluation import Evaluator
from src.demo_data import get_demo_dataset

# Configure Streamlit
st.set_page_config(
    page_title="FRONTLINE — AI Triage",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    /* Color scheme */
    :root {
        --primary: #0d47a1;
        --success: #388e3c;
        --warning: #f57c00;
        --danger: #c62828;
        --neutral: #424242;
    }
    
    /* Global styles */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .stMetric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    
    .priority-p0 {
        color: #c62828;
        font-weight: bold;
    }
    
    .priority-p1 {
        color: #f57c00;
        font-weight: bold;
    }
    
    .priority-p2 {
        color: #0d47a1;
        font-weight: bold;
    }
    
    .priority-p3 {
        color: #388e3c;
        font-weight: bold;
    }
    
    .confidence-high {
        color: #388e3c;
    }
    
    .confidence-low {
        color: #c62828;
    }
    
    .escalated {
        background-color: #fff3e0;
        border-left: 4px solid #f57c00;
        padding: 10px;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state
if "pipeline" not in st.session_state:
    try:
        st.session_state.pipeline = TriagePipeline()
    except Exception as e:
        st.session_state.pipeline = None
        st.error(f"⚠️ LLM Client Error: {str(e)}")

if "results" not in st.session_state:
    st.session_state.results = None

if "dataset" not in st.session_state:
    st.session_state.dataset = None

# Header
st.markdown("""<div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; color: white; margin-bottom: 30px;">
<h1 style="margin: 0; font-size: 3em;">⚡ FRONTLINE</h1>
<p style="margin: 5px 0 0 0; font-size: 1.2em;">AI-Powered Customer Support Triage</p>
<p style="margin: 10px 0 0 0; opacity: 0.9; font-size: 0.9em;">One-Day AI Build Challenge — Production-Grade Classifier</p>
</div>""", unsafe_allow_html=True)

# Main layout
tab1, tab2, tab3, tab4 = st.tabs([
    "🚀 Quick Demo",
    "📊 Batch Process",
    "📈 Evaluation",
    "⚙️ Settings"
])

# ============================================================================
# TAB 1: QUICK DEMO
# ============================================================================
with tab1:
    st.subheader("🎯 Demo Mode — 8 Representative Test Cases")
    st.markdown("See how FRONTLINE handles different scenarios in real-time.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        demo_msgs = get_demo_dataset()
        selected_demo = st.selectbox(
            "Select a demo message:",
            options=[f"[{m['id']}] {m['description'][:50]}" for m in demo_msgs],
            index=0
        )
        demo_idx = int(selected_demo.split("]")[0][1:])
        selected_msg = demo_msgs[demo_idx]
    
    with col2:
        st.metric(
            "📝 Message ID",
            selected_msg["id"],
            delta=None
        )
    
    # Display message
    st.markdown("**Customer Message:**")
    st.code(selected_msg["text"], language="text")
    
    # Classify
    if st.button("🔍 Classify This Message", use_container_width=True, type="primary"):
        if st.session_state.pipeline:
            with st.spinner("⏳ Analyzing message..."):
                result = st.session_state.pipeline.classify_message(
                    selected_msg["id"],
                    selected_msg["text"]
                )
            
            # Display results
            st.success("✅ Classification Complete")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "📂 Category",
                    result.decision.category,
                    delta=None
                )
            
            with col2:
                priority_color = {
                    "P0": "🔴",
                    "P1": "🟠",
                    "P2": "🔵",
                    "P3": "🟢"
                }
                st.metric(
                    "⚡ Priority",
                    f"{priority_color.get(result.decision.priority, '')} {result.decision.priority}",
                    delta=None
                )
            
            with col3:
                conf_pct = int(result.decision.confidence * 100)
                st.metric(
                    "🎯 Confidence",
                    f"{conf_pct}%",
                    delta=None
                )
            
            with col4:
                human_label = "👤 YES" if result.decision.needs_human else "🤖 NO"
                st.metric(
                    "Needs Human",
                    human_label,
                    delta=None
                )
            
            # Summary and action
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**📋 Summary:**")
                st.info(result.decision.summary)
            
            with col2:
                st.markdown("**✅ Suggested Action:**")
                st.info(result.decision.suggested_action)
            
            # Escalation info
            if result.escalation_reason:
                st.markdown("""<div class="escalated">
<strong>⚠️ Escalated to Human Review</strong><br/>
%s
</div>""" % result.escalation_reason, unsafe_allow_html=True)
            
            st.markdown(f"**⏱️ Latency:** {result.latency_ms:.1f}ms")
        else:
            st.error("❌ LLM client not initialized. Check your API key.")

# ============================================================================
# TAB 2: BATCH PROCESSING
# ============================================================================
with tab2:
    st.subheader("📊 Batch Processing")
    st.markdown("Upload a CSV/JSON dataset and process all messages at once.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader(
            "📤 Upload Dataset (CSV/JSON)",
            type=["csv", "json"],
            help="Must contain a 'message' or 'text' column"
        )
    
    with col2:
        st.markdown("**Or try the demo dataset:**")
        if st.button("📌 Load Demo Messages", use_container_width=True):
            demo_data = get_demo_dataset()
            st.session_state.dataset = [
                {"id": m["id"], "text": m["text"]}
                for m in demo_data
            ]
            st.success(f"✅ Loaded {len(demo_data)} demo messages")
    
    # Process dataset
    if st.session_state.dataset or uploaded_file:
        if uploaded_file and not st.session_state.dataset:
            adapter = DatasetAdapter()
            messages, error = adapter.load(uploaded_file.name)
            if error:
                st.error(f"❌ Error loading file: {error}")
            else:
                st.session_state.dataset = messages
                st.success(f"✅ Loaded {len(messages)} messages")
        
        if st.session_state.dataset:
            if st.button("🚀 Process All Messages", use_container_width=True, type="primary"):
                if st.session_state.pipeline:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    with st.spinner("⏳ Processing batch..."):
                        st.session_state.results = st.session_state.pipeline.process_batch(
                            st.session_state.dataset
                        )
                    
                    st.success("✅ Batch Processing Complete")
                else:
                    st.error("❌ Pipeline not initialized")
            
            # Display results summary
            if st.session_state.results:
                results = st.session_state.results
                
                st.markdown("---")
                st.markdown("### 📈 Results Summary")
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric(
                        "Total Messages",
                        results.total_messages,
                        delta=None
                    )
                
                with metric_col2:
                    st.metric(
                        "Successful",
                        results.successful_classifications,
                        delta=f"Failed: {results.failed_classifications}"
                    )
                
                with metric_col3:
                    st.metric(
                        "Escalated to Human",
                        results.escalated_to_human,
                        delta=f"{(results.escalated_to_human/results.total_messages*100):.1f}%"
                    )
                
                with metric_col4:
                    avg_conf_pct = int(results.average_confidence * 100)
                    st.metric(
                        "Avg Confidence",
                        f"{avg_conf_pct}%",
                        delta=f"Latency: {results.average_latency_ms:.0f}ms"
                    )
                
                # Priority distribution
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Priority Distribution:**")
                    priority_data = results.priority_distribution
                    priority_df = pd.DataFrame({
                        "Priority": list(priority_data.keys()),
                        "Count": list(priority_data.values())
                    })
                    st.bar_chart(priority_df.set_index("Priority"))
                
                with col2:
                    st.markdown("**Statistics:**")
                    stats_df = pd.DataFrame({
                        "Metric": ["Success Rate", "Escalation Rate", "Avg Confidence", "Avg Latency (ms)"],
                        "Value": [
                            f"{(results.successful_classifications/results.total_messages*100):.1f}%",
                            f"{(results.escalated_to_human/results.total_messages*100):.1f}%",
                            f"{results.average_confidence:.2f}",
                            f"{results.average_latency_ms:.1f}"
                        ]
                    })
                    st.dataframe(stats_df, use_container_width=True, hide_index=True)
                
                # Browse individual results
                st.markdown("---")
                st.markdown("### 🔍 Browse Individual Results")
                
                result_filter = st.selectbox(
                    "Filter by:",
                    ["All", "P0", "P1", "P2", "P3", "Escalated", "Failed"]
                )
                
                filtered_results = results.results
                if result_filter == "Escalated":
                    filtered_results = [r for r in filtered_results if r.escalation_reason]
                elif result_filter == "Failed":
                    filtered_results = [r for r in filtered_results if r.validation_error]
                elif result_filter.startswith("P"):
                    filtered_results = [r for r in filtered_results if r.decision.priority == result_filter]
                
                # Display paginated results
                if filtered_results:
                    for idx, result in enumerate(filtered_results[:10]):
                        with st.expander(
                            f"🔹 [{result.message_id}] {result.decision.category} • "
                            f"{result.decision.priority} • "
                            f"Conf: {int(result.decision.confidence*100)}%"
                        ):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown("**Message:**")
                                st.text(result.message_text[:200] + ("..." if len(result.message_text) > 200 else ""))
                                
                                st.markdown("**Summary:**")
                                st.info(result.decision.summary)
                                
                                st.markdown("**Action:**")
                                st.info(result.decision.suggested_action)
                            
                            with col2:
                                st.metric("Category", result.decision.category)
                                st.metric("Priority", result.decision.priority)
                                st.metric("Confidence", f"{int(result.decision.confidence*100)}%")
                                st.metric("Needs Human", "✅ YES" if result.decision.needs_human else "❌ NO")
                            
                            if result.escalation_reason:
                                st.warning(f"⚠️ Escalation: {result.escalation_reason}")
                            if result.validation_error:
                                st.error(f"Error: {result.validation_error}")
                
                # Download results
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    # JSON export
                    export_data = {
                        "timestamp": datetime.now().isoformat(),
                        "summary": {
                            "total": results.total_messages,
                            "successful": results.successful_classifications,
                            "failed": results.failed_classifications,
                            "escalated": results.escalated_to_human,
                            "avg_confidence": results.average_confidence,
                            "avg_latency_ms": results.average_latency_ms
                        },
                        "results": [
                            {
                                "id": r.message_id,
                                "decision": r.decision.dict(),
                                "latency_ms": r.latency_ms,
                                "escalation_reason": r.escalation_reason
                            }
                            for r in results.results
                        ]
                    }
                    
                    st.download_button(
                        "⬇️ Download as JSON",
                        json.dumps(export_data, indent=2, ensure_ascii=False),
                        "frontline_results.json",
                        "application/json",
                        use_container_width=True
                    )
                
                with col2:
                    # CSV export
                    csv_data = []
                    for r in results.results:
                        csv_data.append({
                            "message_id": r.message_id,
                            "category": r.decision.category,
                            "priority": r.decision.priority,
                            "confidence": r.decision.confidence,
                            "needs_human": r.decision.needs_human,
                            "latency_ms": r.latency_ms,
                            "escalation_reason": r.escalation_reason or ""
                        })
                    
                    csv_df = pd.DataFrame(csv_data)
                    st.download_button(
                        "⬇️ Download as CSV",
                        csv_df.to_csv(index=False),
                        "frontline_results.csv",
                        "text/csv",
                        use_container_width=True
                    )

# ============================================================================
# TAB 3: EVALUATION
# ============================================================================
with tab3:
    st.subheader("📊 Evaluation Against Ground Truth")
    st.markdown("Compare your predictions against manually labeled ground truth.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gt_file = st.file_uploader(
            "📤 Upload Ground Truth JSON",
            type=["json"],
            key="gt_upload",
            help="Format: [{'message_id': '...', 'category': '...', 'priority': '...', 'needs_human': true|false}, ...]"
        )
    
    if gt_file and st.session_state.results:
        evaluator = Evaluator()
        count, error = evaluator.load_ground_truth(gt_file.name)
        
        if error:
            st.error(f"❌ Error: {error}")
        else:
            st.success(f"✅ Loaded ground truth for {count} messages")
            
            if st.button("📈 Run Evaluation", use_container_width=True, type="primary"):
                metrics = evaluator.evaluate(st.session_state.results.results)
                
                st.success("✅ Evaluation Complete")
                
                # Metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Category Accuracy", f"{metrics.category_agreement:.1f}%")
                
                with col2:
                    st.metric("Priority Accuracy", f"{metrics.priority_agreement:.1f}%")
                
                with col3:
                    st.metric("Needs Human Accuracy", f"{metrics.needs_human_agreement:.1f}%")
                
                with col4:
                    st.metric("Overall Accuracy", f"{metrics.overall_agreement:.1f}%")
                
                # Failures
                if metrics.failures:
                    st.markdown("---")
                    st.markdown(f"### ❌ Failed Cases ({len(metrics.failures)})")
                    
                    for failure in metrics.failures:
                        with st.expander(f"[{failure['message_id']}]"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**Expected:**")
                                st.json(failure['expected'])
                            with col2:
                                st.markdown("**Predicted:**")
                                st.json(failure['predicted'])
    elif not st.session_state.results:
        st.info("💡 Process a dataset first (Batch Process tab) to enable evaluation.")
    else:
        st.info("💡 Upload a ground truth JSON file to run evaluation.")

# ============================================================================
# TAB 4: SETTINGS
# ============================================================================
with tab4:
    st.subheader("⚙️ Configuration")
    
    st.markdown("### API Configuration")
    st.info("🔐 API key is loaded from `ANTHROPIC_API_KEY` environment variable.")
    
    st.markdown("### Escalation Policy")
    if st.session_state.pipeline:
        policy = st.session_state.pipeline.escalation_policy
        
        col1, col2, col3 = st.columns(3)
        with col1:
            new_threshold = st.slider(
                "Confidence Threshold",
                0.0,
                1.0,
                policy.confidence_threshold,
                0.05,
                help="Messages below this confidence are escalated to human"
            )
            if new_threshold != policy.confidence_threshold:
                policy.confidence_threshold = new_threshold
                st.success(f"✅ Updated to {new_threshold}")
        
        with col2:
            escalate_p0_p1 = st.checkbox(
                "Escalate P0/P1 to Human",
                policy.escalate_p0_p1,
                help="Always route critical priorities to human review"
            )
            if escalate_p0_p1 != policy.escalate_p0_p1:
                policy.escalate_p0_p1 = escalate_p0_p1
        
        with col3:
            escalate_unclear = st.checkbox(
                "Escalate Unclear",
                policy.escalate_unclear,
                help="Route unclear cases to human review"
            )
            if escalate_unclear != policy.escalate_unclear:
                policy.escalate_unclear = escalate_unclear
    
    st.markdown("### System Information")
    st.markdown(f"- **App Version**: 0.1.0")
    st.markdown(f"- **Timestamp**: {datetime.now().isoformat()}")
    st.markdown(f"- **Pipeline Status**: {'✅ Ready' if st.session_state.pipeline else '❌ Error'}")
    
    st.markdown("### About FRONTLINE")
    st.markdown("""
    **FRONTLINE** is a production-grade AI customer-support triage classifier built for the One-Day AI Build Challenge.
    
    **Key Features:**
    - 🎯 Structured output validation with Pydantic
    - 🛡️ Prompt injection defense
    - 🚨 Intelligent human escalation
    - 📊 Batch processing with error resilience
    - 🧪 Comprehensive test coverage
    - 📈 Ground truth evaluation
    - 🌍 Multilingual support
    
    **Architecture:**
    - LLM: Claude 3.5 Sonnet (Anthropic)
    - Validation: Pydantic models
    - UI: Streamlit
    - Tests: Pytest
    
    **Repository**: https://github.com/Arpitachoudhary187/frontline-ai-triage
    """)

if __name__ == "__main__":
    pass
