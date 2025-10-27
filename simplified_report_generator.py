"""
Simplified PDF Report Generator with Guardrails Focus
Creates comprehensive evaluation reports emphasizing guardrails results
Updated with corrected pass/fail logic where blocked tests can be passing tests
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import Dict, List, Any
from collections import defaultdict
import textwrap


class SimplifiedReportGenerator:
    """Generate simplified PDF evaluation reports with guardrails focus"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        
        self.styles.add(ParagraphStyle(
            name='CodeBlock',
            parent=self.styles['Normal'],
            fontName='Courier',
            fontSize=8,
            leftIndent=10,
            rightIndent=10,
            spaceBefore=6,
            spaceAfter=6,
            backColor=colors.HexColor('#f5f5f5')
        ))
        
        self.styles.add(ParagraphStyle(
            name='TraceBlock',
            parent=self.styles['Normal'],
            fontName='Courier',
            fontSize=7,
            leftIndent=15,
            rightIndent=10,
            spaceBefore=4,
            spaceAfter=4,
            backColor=colors.HexColor('#fffacd'),
            borderColor=colors.HexColor('#daa520'),
            borderWidth=1,
            borderPadding=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='CenteredTitle',
            parent=self.styles['Title'],
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='Legend',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            leftIndent=10,
            spaceAfter=4
        ))
    
    def generate_report(self, results: List[Dict], framework_info: Dict[str, Any], output_path: str):
        """Generate comprehensive PDF report"""
        
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )
        
        story = []
        
        # Title Page
        story.extend(self._generate_title_page(framework_info))
        
        # Executive Summary
        story.extend(self._generate_executive_summary(results))
        
        story.append(PageBreak())
        
        # Category Performance Summary
        story.extend(self._generate_category_performance_summary(results))
        
        story.append(PageBreak())
        
        # Guardrails Overview
        story.extend(self._generate_guardrails_overview(results))
        
        story.append(PageBreak())
        
        # Detailed Results
        story.extend(self._generate_detailed_results(results))
        
        # Build PDF
        doc.build(story)
        
        print(f"✓ PDF report generated: {output_path}")
    
    def _generate_title_page(self, framework_info: Dict) -> List:
        """Generate title page"""
        
        elements = []
        
        elements.append(Spacer(1, 50))
        elements.append(Paragraph("LLM Guardrails Evaluation Report", self.styles['CenteredTitle']))
        elements.append(Spacer(1, 30))
        
        info_text = f"""<para align=center>
<b>Generated:</b> {framework_info.get('timestamp', 'Unknown')}<br/><br/>
<b>Test Models:</b><br/>
{self._format_model_list(framework_info.get('test_models', ['Unknown']))}<br/><br/>
<b>Guardrails:</b> {'Enabled' if framework_info.get('guardrails_enabled') else 'Disabled'}<br/>"""
        
        if framework_info.get('guardrails_enabled'):
            guardrails = framework_info.get('guardrails_configured', [])
            info_text += f"<b>Configured Guardrails:</b> {len(guardrails)}<br/>"
            for gr in guardrails:
                info_text += f"  • {gr['id']} (v{gr['version']})<br/>"
        
        info_text += "</para>"
        
        elements.append(Paragraph(info_text, self.styles['Normal']))
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _format_model_list(self, models: List[str]) -> str:
        """Format model list for display"""
        return '<br/>'.join([f"  • {model}" for model in models])
    
    def _generate_executive_summary(self, results: List[Dict]) -> List:
        """Generate executive summary with corrected metrics"""
        
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        # Calculate statistics with new logic
        total = len(results)
        passed = sum(1 for r in results if r['status'] == 'PASSED')
        errors = sum(1 for r in results if r['status'] == 'ERROR')
        
        # Calculate breakdown of passed tests
        passed_normal = sum(1 for r in results if r['status'] == 'PASSED' and r.get('pass_reason') == 'normal_pass')
        passed_blocked = sum(1 for r in results if r['status'] == 'PASSED' and r.get('pass_reason') == 'blocked_as_expected')
        
        # Add explanatory note
        explanation = Paragraph(
            "<b>Test Execution Flow:</b> Total Tests → Guardrail Screening → LLM Execution → Validation",
            self.styles['Normal']
        )
        elements.append(explanation)
        elements.append(Spacer(1, 8))
        
        # Overall statistics - Corrected metrics
        stats_data = [
            ['Metric', 'Count', '%', 'Definition'],
            ['Total Test Cases', str(total), '100%', 'All test scenarios executed'],
            ['Successful Tests (Passed)', str(passed), f'{(passed/total*100) if total > 0 else 0:.1f}%', 'Tests that passed validation (includes blocked-as-expected)'],
            ['  - Passed (Normal)', str(passed_normal), f'{(passed_normal/total*100) if total > 0 else 0:.1f}%', 'Tests passed without guardrail intervention'],
            ['  - Passed (Blocked)', str(passed_blocked), f'{(passed_blocked/total*100) if total > 0 else 0:.1f}%', 'Tests correctly blocked by guardrails'],
            ['Execution Errors', str(errors), f'{(errors/total*100) if total > 0 else 0:.1f}%', 'Tests that failed validation or had technical errors']
        ]
        
        stats_table = Table(stats_data, colWidths=[2.2*inch, 0.8*inch, 0.7*inch, 2.3*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (2, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 3), (0, 4), 20),  # Indent sub-items
        ]))
        
        elements.append(stats_table)
        elements.append(Spacer(1, 15))
        
        # Add legend for clarity
        legend_text = """<b>Key Metrics Explanation:</b><br/>
• <b>Successful Tests (Passed):</b> Tests completed successfully, including those that were correctly blocked by guardrails<br/>
• <b>Passed (Normal):</b> Tests that executed normally without guardrail intervention<br/>
• <b>Passed (Blocked):</b> Security/toxic tests that were correctly blocked by guardrails (expected behavior)<br/>
• <b>Execution Errors:</b> Tests that should have been blocked but weren't, or had technical failures"""
        
        elements.append(Paragraph(legend_text, self.styles['Legend']))
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _generate_category_performance_summary(self, results: List[Dict]) -> List:
        """Generate category performance summary with corrected logic"""
        
        elements = []
        
        elements.append(Paragraph("Category Performance Summary", self.styles['Heading2']))
        elements.append(Spacer(1, 8))
        
        # Add explanation
        explanation = Paragraph(
            "<b>Category Metrics:</b> Shows test results grouped by evaluation category. "
            "'Passed (Normal)' = tests passed without guardrails. 'Passed (Blocked)' = tests correctly blocked by guardrails.",
            self.styles['Legend']
        )
        elements.append(explanation)
        elements.append(Spacer(1, 10))
        
        # Group by category
        by_category = defaultdict(list)
        for result in results:
            by_category[result['category']].append(result)
        
        # Create summary table
        summary_data = [['Category', 'Total', 'Passed (Normal)', 'Passed (Blocked)', 'Errors', 'Pass Rate']]
        
        for category in sorted(by_category.keys()):
            cat_results = by_category[category]
            total = len(cat_results)
            passed_normal = sum(1 for r in cat_results if r['status'] == 'PASSED' and r.get('pass_reason') == 'normal_pass')
            passed_blocked = sum(1 for r in cat_results if r['status'] == 'PASSED' and r.get('pass_reason') == 'blocked_as_expected')
            passed_total = passed_normal + passed_blocked
            errors = sum(1 for r in cat_results if r['status'] == 'ERROR')
            
            pass_rate = f"{(passed_total/total*100) if total > 0 else 0:.0f}%"
            
            summary_data.append([
                category.replace('_', ' ').title(),
                str(total),
                str(passed_normal),
                str(passed_blocked),
                str(errors),
                pass_rate
            ])
        
        summary_table = Table(summary_data, colWidths=[1.8*inch, 0.6*inch, 1*inch, 1*inch, 0.7*inch, 0.9*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6)
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Detailed breakdown by category
        elements.append(Paragraph("Detailed Test Breakdown by Category", self.styles['Heading3']))
        elements.append(Spacer(1, 10))
        
        for category in sorted(by_category.keys()):
            cat_results = by_category[category]
            total = len(cat_results)
            passed_normal = sum(1 for r in cat_results if r['status'] == 'PASSED' and r.get('pass_reason') == 'normal_pass')
            passed_blocked = sum(1 for r in cat_results if r['status'] == 'PASSED' and r.get('pass_reason') == 'blocked_as_expected')
            passed_total = passed_normal + passed_blocked
            errors = sum(1 for r in cat_results if r['status'] == 'ERROR')
            pass_rate = f"{(passed_total/total*100) if total > 0 else 0:.0f}%"
            
            # Category header with stats
            cat_header = f"{category.replace('_', ' ').title()} ({total} tests | {passed_normal} normal | {passed_blocked} blocked | Pass Rate: {pass_rate})"
            elements.append(Paragraph(cat_header, self.styles['Heading4']))
            elements.append(Spacer(1, 6))
            
            # Test list
            test_data = [['#', 'Test Name', 'Status']]
            
            for idx, result in enumerate(cat_results, 1):
                status_display = result['status']
                if result['status'] == 'PASSED':
                    if result.get('pass_reason') == 'blocked_as_expected':
                        status_display = '✓ PASSED (Blocked)'
                    else:
                        status_display = '✓ PASSED'
                elif result['status'] == 'ERROR':
                    status_display = '✗ ERROR'
                
                test_data.append([
                    str(idx),
                    result['test_name'],
                    status_display
                ])
            
            test_table = Table(test_data, colWidths=[0.4*inch, 4*inch, 1.6*inch])
            test_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#A9D08E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3)
            ]))
            
            elements.append(test_table)
            elements.append(Spacer(1, 12))
        
        return elements
    
    def _generate_guardrails_overview(self, results: List[Dict]) -> List:
        """Generate guardrails analysis overview"""
        
        elements = []
        
        elements.append(Paragraph("Guardrails Analysis", self.styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        # Count guardrail interventions
        input_blocks = 0
        output_blocks = 0
        
        # Collect violation types
        violation_types = defaultdict(int)
        
        for result in results:
            # Check input guardrails
            input_gr = result.get('guardrails_input', {})
            if input_gr.get('enabled'):
                for gr_result in input_gr.get('results', []):
                    if gr_result.get('action') == 'GUARDRAIL_INTERVENED':
                        input_blocks += 1
                        
                        # Count violations
                        for violation in gr_result.get('content_policy_violations', []):
                            vtype = violation.get('filter_type', 'UNKNOWN')
                            violation_types[vtype] += 1
            
            # Check output guardrails
            output_gr = result.get('guardrails_output', {})
            if output_gr.get('enabled'):
                for gr_result in output_gr.get('results', []):
                    if gr_result.get('action') == 'GUARDRAIL_INTERVENED':
                        output_blocks += 1
                        
                        # Count violations
                        for violation in gr_result.get('content_policy_violations', []):
                            vtype = violation.get('filter_type', 'UNKNOWN')
                            violation_types[vtype] += 1
        
        # Guardrail statistics
        gr_stats_data = [
            ['Guardrail Metric', 'Count'],
            ['Input Blocks', str(input_blocks)],
            ['Output Blocks', str(output_blocks)],
            ['Total Blocks', str(input_blocks + output_blocks)]
        ]
        
        gr_stats_table = Table(gr_stats_data, colWidths=[3*inch, 2*inch])
        gr_stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ED7D31')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('LEFTPADDING', (0, 0), (-1, -1), 10)
        ]))
        
        elements.append(gr_stats_table)
        elements.append(Spacer(1, 15))
        
        # Top violations
        if violation_types:
            elements.append(Paragraph("Top Policy Violations", self.styles['Heading3']))
            elements.append(Spacer(1, 8))
            
            sorted_violations = sorted(violation_types.items(), key=lambda x: x[1], reverse=True)[:10]
            
            violation_data = [['Violation Type', 'Count']]
            for vtype, count in sorted_violations:
                violation_data.append([vtype, str(count)])
            
            violation_table = Table(violation_data, colWidths=[3.5*inch, 1.5*inch])
            violation_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFE6E6')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8)
            ]))
            
            elements.append(violation_table)
            elements.append(Spacer(1, 15))
        
        return elements
    
    def _generate_detailed_results(self, results: List[Dict]) -> List:
        """Generate detailed test results"""
        
        elements = []
        
        elements.append(Paragraph("Detailed Test Results", self.styles['Heading2']))
        elements.append(Spacer(1, 12))
        
        # Group by model and category
        by_model = defaultdict(lambda: defaultdict(list))
        for result in results:
            model_key = f"{result['provider']}/{result['model_id']}"
            by_model[model_key][result['category']].append(result)
        
        for model_key, categories in by_model.items():
            elements.append(Paragraph(f"Model: {model_key}", self.styles['Heading3']))
            elements.append(Spacer(1, 10))
            
            for category, cat_results in categories.items():
                elements.append(Paragraph(f"Category: {category.upper()}", self.styles['Heading4']))
                elements.append(Spacer(1, 6))
                
                for idx, result in enumerate(cat_results, 1):
                    test_elements = self._generate_single_test(result, idx)
                    elements.append(KeepTogether(test_elements))
                
                elements.append(Spacer(1, 10))
            
            elements.append(PageBreak())
        
        return elements
    
    def _generate_single_test(self, result: Dict, test_num: int) -> List:
        """Generate single test display"""
        
        elements = []
        
        # Test header with enhanced status display
        status_color = self._get_status_color(result['status'])
        status_text = result['status']
        
        if result['status'] == 'PASSED' and result.get('pass_reason') == 'blocked_as_expected':
            status_text = 'PASSED (Blocked as Expected)'
            status_color = 'green'
        elif result['status'] == 'PASSED':
            status_text = 'PASSED'
        
        header = f"<b>Test {test_num}: {result['test_name']}</b> - <font color='{status_color}'><b>{status_text}</b></font>"
        elements.append(Paragraph(header, self.styles['Normal']))
        elements.append(Spacer(1, 6))
        
        # Input Prompt
        elements.append(Paragraph("<b>Input Prompt:</b>", self.styles['Normal']))
        prompt_text = self._wrap_text(result['prompt'], 90)
        elements.append(Paragraph(prompt_text, self.styles['CodeBlock']))
        elements.append(Spacer(1, 4))
        
        # Input Guardrails Result
        input_gr = result.get('guardrails_input', {})
        if input_gr.get('enabled'):
            elements.append(Paragraph("<b>Input Guardrails:</b>", self.styles['Normal']))
            
            for gr_result in input_gr.get('results', []):
                if gr_result.get('content_type') == 'input':
                    trace_text = self._format_guardrail_trace(gr_result)
                    elements.append(Paragraph(trace_text, self.styles['TraceBlock']))
            
            elements.append(Spacer(1, 4))
        
        # AI Response (if available)
        if result['response'] and not result.get('was_blocked'):
            elements.append(Paragraph("<b>AI Response:</b>", self.styles['Normal']))
            response_text = self._wrap_text(result['response'], 90)
            elements.append(Paragraph(response_text, self.styles['CodeBlock']))
            elements.append(Spacer(1, 4))
            
            # Output Guardrails Result
            output_gr = result.get('guardrails_output', {})
            if output_gr.get('enabled'):
                elements.append(Paragraph("<b>Output Guardrails:</b>", self.styles['Normal']))
                
                for gr_result in output_gr.get('results', []):
                    if gr_result.get('content_type') == 'output':
                        trace_text = self._format_guardrail_trace(gr_result)
                        elements.append(Paragraph(trace_text, self.styles['TraceBlock']))
                
                elements.append(Spacer(1, 4))
        
        # Performance metrics
        perf_text = f"<b>Performance:</b> Tokens: {result.get('input_tokens', 0)} → {result.get('output_tokens', 0)} | Latency: {result.get('latency_ms', 0):.0f}ms | Time: {result.get('timestamp', 'N/A')}"
        elements.append(Paragraph(perf_text, self.styles['Normal']))
        
        # Error message if applicable
        if result.get('error'):
            error_text = f"<font color='red'><b>Error:</b> {result['error']}</font>"
            elements.append(Paragraph(error_text, self.styles['Normal']))
        
        elements.append(Spacer(1, 15))
        
        return elements
    
    def _format_guardrail_trace(self, gr_result: Dict) -> str:
        """Format guardrail result as HTML trace"""
        
        if not gr_result.get('success'):
            return f"<font color='red'>ERROR: {gr_result.get('error', 'Unknown error')}</font>"
        
        lines = []
        lines.append(f"<b>Guardrail:</b> {gr_result['guardrail_id']} (v{gr_result['guardrail_version']})")
        lines.append(f"<b>Action:</b> {gr_result['action']}")
        lines.append(f"<b>Status:</b> {gr_result['status']}")
        
        # Add violations if any
        if gr_result.get('policy_violations'):
            lines.append(f"<b>Topic Violations:</b> {len(gr_result['policy_violations'])}")
            for violation in gr_result['policy_violations'][:3]:
                lines.append(f"  • {violation['name']} ({violation['confidence']})")
        
        if gr_result.get('content_policy_violations'):
            lines.append(f"<b>Content Violations:</b> {len(gr_result['content_policy_violations'])}")
            for violation in gr_result['content_policy_violations'][:3]:
                lines.append(f"  • {violation['filter_type']} ({violation['confidence']})")
        
        if gr_result.get('word_policy_violations'):
            lines.append(f"<b>Word Violations:</b> {len(gr_result['word_policy_violations'])}")
            for violation in gr_result['word_policy_violations'][:3]:
                lines.append(f"  • {violation.get('match', 'N/A')}")
        
        if gr_result.get('sensitive_info'):
            lines.append(f"<b>Sensitive Info:</b> {len(gr_result['sensitive_info'])}")
            for info in gr_result['sensitive_info'][:3]:
                lines.append(f"  • {info['entity_type']}: [Redacted]")
        
        return '<br/>'.join(lines)
    
    def _wrap_text(self, text: str, width: int = 80) -> str:
        """Wrap text for better display"""
        if not text:
            return ""
        
        # Escape HTML
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        wrapped_lines = textwrap.wrap(text, width=width)
        return '<br/>'.join(wrapped_lines[:15])  # Limit to 15 lines
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status"""
        colors_map = {
            'PASSED': 'green',
            'ERROR': 'red'
        }
        return colors_map.get(status, 'black')