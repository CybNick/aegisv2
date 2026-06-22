"""Core reporting engine logic for Milestone 7.

Generates Executive and Technical reports deterministically.
Uses pure python formatters (no external templating engines) to maintain
local-first, zero-dependency architectural constraints.
"""

from __future__ import annotations

import json
import csv
import io
import html
from typing import Any

from backend.analysis.query import GraphView
from backend.analysis.risk import RiskAnalyzer
from backend.analysis.exposure import ExposureAnalyzer
from backend.analysis.criticality import CriticalityAnalyzer
from backend.reporting.schemas import ReportFormat, ReportType, ReportResult
from backend.graph.model import NodeType

from backend.intelligence.classification.classifier import classify_environment
from backend.intelligence.classification.criticality import calculate_business_criticality
from backend.intelligence.classification.data_sensitivity import classify_data_sensitivity
from backend.intelligence.classification.ownership import resolve_ownership
from backend.intelligence.recommendations.recommendation_engine import RecommendationEngine
from backend.intelligence.compliance.compliance_engine import ComplianceEngine
from backend.intelligence.governance.governance_engine import GovernanceEngine
from backend.intelligence.trends.trend_engine import TrendEngine
from backend.analysis.query import QueryEngine
from backend.intelligence.assistant.assistant_service import AssistantService


class ReportingEngine:
    """Core reporting engine."""

    def __init__(self, view: GraphView) -> None:
        self.view = view
        self.as_of = view.as_of
        self.context = view.context

    def generate(self, report_type: ReportType, fmt: ReportFormat) -> ReportResult:
        """Generate a report of the given type and format."""
        if report_type == ReportType.EXECUTIVE:
            data = self._gather_executive_data()
        elif report_type == ReportType.TECHNICAL:
            data = self._gather_technical_data()
        elif report_type == ReportType.ASSET_INVENTORY:
            data = self._gather_asset_inventory()
        elif report_type == ReportType.CRITICAL_ASSETS:
            data = self._gather_critical_assets()
        elif report_type == ReportType.SENSITIVE_DATA:
            data = self._gather_sensitive_data()
        elif report_type == ReportType.EXECUTIVE_ACTION_PLAN:
            data = self._gather_action_plan()
        elif report_type == ReportType.RISK_REMEDIATION:
            data = self._gather_remediation()
        elif report_type == ReportType.CRITICAL_FINDINGS:
            data = self._gather_critical_findings()
        elif report_type == ReportType.OWNERSHIP:
            data = self._gather_ownership()
        elif report_type == ReportType.EXECUTIVE_BOARD_REPORT:
            data = self._gather_executive_board()
        elif report_type == ReportType.COMPLIANCE_REPORT:
            data = self._gather_compliance()
        elif report_type == ReportType.RISK_TREND_REPORT:
            data = self._gather_risk_trend()
        elif report_type == ReportType.GOVERNANCE_REPORT:
            data = self._gather_governance()
        elif report_type == ReportType.AI_EXECUTIVE_SUMMARY:
            data = self._gather_ai_executive_summary()
        elif report_type == ReportType.AI_RISK_NARRATIVE:
            data = self._gather_ai_risk_narrative()
        elif report_type == ReportType.AI_COMPLIANCE_NARRATIVE:
            data = self._gather_ai_compliance_narrative()
        else:
            raise ValueError(f"Unsupported report type: {report_type}")

        if fmt == ReportFormat.JSON:
            content = data
        elif fmt == ReportFormat.MARKDOWN:
            content = self._render_markdown(report_type, data)
        elif fmt == ReportFormat.HTML:
            content = self._render_html(report_type, data)
        elif fmt == ReportFormat.CSV:
            content = self._render_csv(report_type, data)
        else:
            raise ValueError(f"Unsupported format: {fmt}")

        return ReportResult(
            report_type=report_type,
            format=fmt,
            as_of=self.as_of,
            context=self.context,
            content=content,
            metadata={"node_count": data.get("total_nodes", 0)}
        )

    def _gather_executive_data(self) -> dict[str, Any]:
        """Gather high-level executive data."""
        risk_findings = list(RiskAnalyzer().analyze(self.view))
        critical_findings = list(CriticalityAnalyzer().analyze(self.view))
        exposure_findings = list(ExposureAnalyzer().analyze(self.view))

        high_risk = sum(1 for f in risk_findings if f.category == "CRITICAL" or f.category == "HIGH")
        total_assets = len(self.view.nodes_of_type(NodeType.ASSET))

        return {
            "title": "Aegis Executive Summary",
            "total_nodes": len(self.view.live_node_ids()),
            "total_assets": total_assets,
            "high_risk_count": high_risk,
            "critical_assets": len(critical_findings),
            "exposures_detected": len(exposure_findings),
            "top_risks": [f.to_dict() for f in risk_findings[:10]]
        }

    def _gather_technical_data(self) -> dict[str, Any]:
        """Gather detailed technical data."""
        nodes = []
        for nid in sorted(self.view.live_node_ids()):
            n = self.view.node(nid)
            if n: 
                d = n.to_dict()
                d["value"] = self.view.value_of(nid)
                nodes.append(d)

        risk_findings = list(RiskAnalyzer().analyze(self.view))
        
        return {
            "title": "Aegis Technical Report",
            "total_nodes": len(nodes),
            "nodes": nodes,
            "risks": [f.to_dict() for f in risk_findings]
        }

    def _gather_asset_inventory(self) -> dict[str, Any]:
        assets = []
        for nid in self.view.live_node_ids():
            node = self.view.node(nid)
            if node and node.node_type.value in ["ASSET", "DATASTORE", "SERVICE"]:
                env = classify_environment(self.view, nid)
                assets.append({"id": nid, "type": node.node_type.value, "environment": env})
        return {"title": "Asset Inventory", "assets": assets}

    def _gather_critical_assets(self) -> dict[str, Any]:
        critical = []
        for nid in self.view.live_node_ids():
            crit = calculate_business_criticality(self.view, nid)
            if crit["level"] in ["High", "Critical"]:
                critical.append({"id": nid, "criticality": crit["level"], "score": crit["score"]})
        critical.sort(key=lambda x: x["score"], reverse=True)
        return {"title": "Critical Assets Report", "critical": critical}

    def _gather_sensitive_data(self) -> dict[str, Any]:
        sensitive = []
        for nid in self.view.live_node_ids():
            level, conf, ev = classify_data_sensitivity(self.view, nid)
            if level in ["Restricted", "Confidential"]:
                sensitive.append({"id": nid, "sensitivity": level})
        return {"title": "Sensitive Data Report", "sensitive": sensitive}

    def _gather_action_plan(self) -> dict[str, Any]:
        recs = RecommendationEngine(self.view).generate()
        top = [r for r in recs if r.severity.value in ["CRITICAL", "HIGH"]]
        return {"title": "Executive Action Plan", "recommendations": [r.model_dump() for r in top]}

    def _gather_remediation(self) -> dict[str, Any]:
        recs = RecommendationEngine(self.view).generate()
        return {"title": "Risk Remediation Report", "recommendations": [r.model_dump() for r in recs]}

    def _gather_critical_findings(self) -> dict[str, Any]:
        recs = [r for r in RecommendationEngine(self.view).generate() if r.severity.value == "CRITICAL"]
        return {"title": "Critical Findings Report", "findings": [r.model_dump() for r in recs]}

    def _gather_ownership(self) -> dict[str, Any]:
        owners = []
        for nid in self.view.live_node_ids():
            own = resolve_ownership(self.view, nid)
            if any(own.values()):
                owners.append({"id": nid, "team": own.get("team"), "technical": own.get("technical"), "business": own.get("business")})
        return {"title": "Ownership Report", "owners": owners}

    def _gather_executive_board(self) -> dict[str, Any]:
        risk_findings = list(RiskAnalyzer().analyze(self.view))
        critical = sum(1 for f in risk_findings if f.category == "CRITICAL")
        compliance = ComplianceEngine(self.view).generate()["overall_score"]
        return {
            "title": "Executive Board Report",
            "total_assets": len(self.view.nodes_of_type(NodeType.ASSET)),
            "critical_risks": critical,
            "compliance_score": compliance
        }
        
    def _gather_compliance(self) -> dict[str, Any]:
        comp = ComplianceEngine(self.view).generate()
        return {"title": "Compliance Report", "compliance": comp}

    def _gather_risk_trend(self) -> dict[str, Any]:
        # Create a basic query engine from store? We only have self.view, but that's a snapshot.
        # This is tricky because we only passed a view to the ReportingEngine. 
        # But we can just emit the current view's risk to not break the abstraction.
        # Alternatively, we could assume we just show the snapshot data.
        risk_findings = list(RiskAnalyzer().analyze(self.view))
        total_risk = sum(r.score for r in risk_findings)
        return {"title": "Risk Trend Report", "total_risk": total_risk}

    def _gather_governance(self) -> dict[str, Any]:
        gov = GovernanceEngine(self.view).generate()
        return {"title": "Governance Report", "findings": gov}
        
    def _gather_ai_executive_summary(self) -> dict[str, Any]:
        assistant = AssistantService(QueryEngine(self.view.graph), context=self.context, as_of=self.as_of)
        res = assistant.ask("Generate executive summary")
        return {"title": "AI Executive Summary", "narrative": res["response"]}
        
    def _gather_ai_risk_narrative(self) -> dict[str, Any]:
        assistant = AssistantService(QueryEngine(self.view.graph), context=self.context, as_of=self.as_of)
        res = assistant.ask("What is my highest risk?")
        return {"title": "AI Risk Narrative", "narrative": res["response"]}
        
    def _gather_ai_compliance_narrative(self) -> dict[str, Any]:
        assistant = AssistantService(QueryEngine(self.view.graph), context=self.context, as_of=self.as_of)
        res = assistant.ask("Are we compliant?")
        return {"title": "AI Compliance Narrative", "narrative": res["response"]}

    def _render_markdown(self, report_type: ReportType, data: dict[str, Any]) -> str:
        """Render data to Markdown."""
        lines = [f"# {data['title']}", f"**As of**: {self.as_of}", f"**Context**: {self.context}", ""]
        
        if report_type == ReportType.EXECUTIVE:
            lines.append("## Summary")
            lines.append(f"- **Total Assets**: {data['total_assets']}")
            lines.append(f"- **Critical Assets**: {data['critical_assets']}")
            lines.append(f"- **Exposures Detected**: {data['exposures_detected']}")
            lines.append(f"- **High/Critical Risks**: {data['high_risk_count']}")
            lines.append("")
            lines.append("## Top Risks")
            for r in data["top_risks"]:
                lines.append(f"- **{r['entity_id']}**: Score {r['score']} ({r['category']})")
        
        elif report_type == ReportType.TECHNICAL:
            lines.append("## Nodes Inventory")
            for n in data["nodes"]:
                key_str = json.dumps(n.get('key', {}))
                val_str = json.dumps(n.get('value', {}))
                lines.append(f"- `{n['id']}` [{n['type']}]: {key_str} - {val_str}")
            lines.append("")
            lines.append("## All Risks")
            for r in data["risks"]:
                lines.append(f"- **{r['entity_id']}**: Score {r['score']} ({r['category']})")

        elif report_type == ReportType.ASSET_INVENTORY:
            lines.append("## Assets")
            for a in data["assets"]:
                lines.append(f"- **{a['id']}** ({a['type']}): {a['environment']}")
                
        elif report_type == ReportType.CRITICAL_ASSETS:
            lines.append("## Critical Assets")
            for c in data["critical"]:
                lines.append(f"- **{c['id']}**: {c['criticality']} (Score: {c['score']})")
                
        elif report_type == ReportType.SENSITIVE_DATA:
            lines.append("## Sensitive Data Repositories")
            for s in data["sensitive"]:
                lines.append(f"- **{s['id']}**: {s['sensitivity']}")
                
        elif report_type in [ReportType.EXECUTIVE_ACTION_PLAN, ReportType.RISK_REMEDIATION]:
            lines.append("## Recommendations")
            for r in data["recommendations"]:
                lines.append(f"- **[{r['severity']}] {r['title']}**")
                lines.append(f"  - Reason: {r['description']}")
                lines.append(f"  - Action: {r['actions'][0]}")

        elif report_type == ReportType.CRITICAL_FINDINGS:
            lines.append("## Critical Findings")
            for f in data["findings"]:
                lines.append(f"- **{f['title']}**: {f['description']}")

        elif report_type == ReportType.OWNERSHIP:
            lines.append("## Asset Ownership")
            for o in data["owners"]:
                lines.append(f"- **{o['id']}**: Team={o['team']}, Tech={o['technical']}, Biz={o['business']}")

        elif report_type == ReportType.EXECUTIVE_BOARD_REPORT:
            lines.append(f"- **Total Assets**: {data['total_assets']}")
            lines.append(f"- **Critical Risks**: {data['critical_risks']}")
            lines.append(f"- **Compliance Score**: {data['compliance_score']}%")
            
        elif report_type == ReportType.COMPLIANCE_REPORT:
            lines.append(f"## Overall Score: {data['compliance']['overall_score']}%")
            for fw, fw_data in data['compliance']['frameworks'].items():
                lines.append(f"### {fw}: {fw_data['score']}%")
                for c in fw_data['failed_controls']:
                    lines.append(f"- [FAILED] {c['control']['id']}: {c['reason']}")
                    
        elif report_type == ReportType.RISK_TREND_REPORT:
            lines.append(f"## Current Total Risk: {data['total_risk']}")
            
        elif report_type == ReportType.GOVERNANCE_REPORT:
            lines.append("## Governance Findings")
            for f in data["findings"]:
                lines.append(f"- **[{f['severity']}] {f['title']}**: {f['target_name']} -> {f['action']}")

        elif report_type in [ReportType.AI_EXECUTIVE_SUMMARY, ReportType.AI_RISK_NARRATIVE, ReportType.AI_COMPLIANCE_NARRATIVE]:
            n = data["narrative"]
            lines.append(f"## {n['title']}")
            for f in n["findings"]:
                lines.append(f"### {f['title']} (Severity: {f.get('severity', 'INFO')})")
                lines.append(f"- **Evidence**: {f.get('evidence', '')}")
                lines.append(f"- **Action**: {f.get('action', '')}")
                if f.get('affected_assets'):
                    lines.append(f"- **Assets**: {', '.join(f['affected_assets'])}")

        return "\n".join(lines)

    def _render_html(self, report_type: ReportType, data: dict[str, Any]) -> str:
        """Render data to simple HTML."""
        md = self._render_markdown(report_type, data)
        # Minimal MD to HTML (since no external deps)
        html_lines = ["<!DOCTYPE html><html><head><title>Aegis Report</title></head><body>"]
        for line in md.split("\\n"):
            if line.startswith("# "): html_lines.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "): html_lines.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.startswith("- "): html_lines.append(f"<li>{html.escape(line[2:])}</li>")
            elif line.strip() == "": html_lines.append("<br>")
            else: html_lines.append(f"<p>{html.escape(line)}</p>")
        html_lines.append("</body></html>")
        return "\\n".join(html_lines)

    def _render_csv(self, report_type: ReportType, data: dict[str, Any]) -> str:
        """Render data to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        if report_type == ReportType.EXECUTIVE:
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Assets", data["total_assets"]])
            writer.writerow(["Critical Assets", data["critical_assets"]])
            writer.writerow(["Exposures Detected", data["exposures_detected"]])
            writer.writerow(["High Risk Count", data["high_risk_count"]])
            writer.writerow([])
            writer.writerow(["Entity ID", "Risk Score", "Category"])
            for r in data["top_risks"]:
                writer.writerow([r["entity_id"], r["score"], r["category"]])
                
        elif report_type == ReportType.TECHNICAL:
            writer.writerow(["Entity ID", "Type"])
            for n in data["nodes"]:
                writer.writerow([n["id"], n["type"]])
            writer.writerow([])
            writer.writerow(["Entity ID", "Risk Score", "Category"])
            for r in data["risks"]:
                writer.writerow([r["entity_id"], r["score"], r["category"]])

        elif report_type == ReportType.ASSET_INVENTORY:
            writer.writerow(["Entity ID", "Type", "Environment"])
            for a in data["assets"]:
                writer.writerow([a["id"], a["type"], a["environment"]])
                
        elif report_type == ReportType.CRITICAL_ASSETS:
            writer.writerow(["Entity ID", "Criticality", "Score"])
            for c in data["critical"]:
                writer.writerow([c["id"], c["criticality"], c["score"]])
                
        elif report_type == ReportType.SENSITIVE_DATA:
            writer.writerow(["Entity ID", "Sensitivity"])
            for s in data["sensitive"]:
                writer.writerow([s["id"], s["sensitivity"]])
                
        elif report_type in [ReportType.EXECUTIVE_ACTION_PLAN, ReportType.RISK_REMEDIATION]:
            writer.writerow(["ID", "Severity", "Title", "Description", "Primary Action"])
            for r in data["recommendations"]:
                writer.writerow([r["id"], r["severity"], r["title"], r["description"], r["actions"][0] if r["actions"] else ""])

        elif report_type == ReportType.CRITICAL_FINDINGS:
            writer.writerow(["ID", "Title", "Description", "Category"])
            for f in data["findings"]:
                writer.writerow([f["id"], f["title"], f["description"], f["category"]])

        elif report_type == ReportType.OWNERSHIP:
            writer.writerow(["Entity ID", "Team Owner", "Technical Owner", "Business Owner"])
            for o in data["owners"]:
                writer.writerow([o["id"], o["team"], o["technical"], o["business"]])
                
        elif report_type == ReportType.EXECUTIVE_BOARD_REPORT:
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Assets", data["total_assets"]])
            writer.writerow(["Critical Risks", data["critical_risks"]])
            writer.writerow(["Compliance Score", data["compliance_score"]])
            
        elif report_type == ReportType.COMPLIANCE_REPORT:
            writer.writerow(["Framework", "Score", "Failed Control", "Reason"])
            for fw, fw_data in data['compliance']['frameworks'].items():
                if not fw_data['failed_controls']:
                    writer.writerow([fw, fw_data['score'], "None", ""])
                for c in fw_data['failed_controls']:
                    writer.writerow([fw, fw_data['score'], c['control']['id'], c['reason']])
                    
        elif report_type == ReportType.RISK_TREND_REPORT:
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Total Risk", data["total_risk"]])
            
        elif report_type == ReportType.GOVERNANCE_REPORT:
            writer.writerow(["ID", "Severity", "Title", "Target", "Action", "Category"])
            for f in data["findings"]:
                writer.writerow([f["id"], f["severity"], f["title"], f["target_name"], f["action"], f["category"]])
                
        elif report_type in [ReportType.AI_EXECUTIVE_SUMMARY, ReportType.AI_RISK_NARRATIVE, ReportType.AI_COMPLIANCE_NARRATIVE]:
            writer.writerow(["Finding Title", "Severity", "Evidence", "Action"])
            for f in data["narrative"]["findings"]:
                writer.writerow([f["title"], f.get("severity", "INFO"), f.get("evidence", ""), f.get("action", "")])
                
        return output.getvalue()
