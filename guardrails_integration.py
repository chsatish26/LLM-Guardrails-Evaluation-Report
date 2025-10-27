"""
AWS Bedrock Guardrails Integration Module
Evaluates prompts and responses using AWS Bedrock Guardrails
"""

import os
import json
import boto3
from typing import Dict, List, Any, Optional
from datetime import datetime


class GuardrailsIntegration:
    """AWS Bedrock Guardrails evaluation"""
    
    def __init__(self):
        self.enabled = os.getenv('GUARDRAILS_ENABLED', 'false').lower() == 'true'
        self.mode = os.getenv('GUARDRAILS_MODE', 'both').lower()
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        
        # Parse guardrail IDs
        self.guardrails = []
        guardrails_config = os.getenv('GUARDRAILS_IDS', '')
        
        if guardrails_config:
            for config in guardrails_config.split(','):
                config = config.strip()
                if ':' in config:
                    guardrail_id, version = config.split(':', 1)
                    self.guardrails.append({
                        'id': guardrail_id.strip(),
                        'version': version.strip()
                    })
        
        if self.enabled and self.guardrails:
            # Initialize Bedrock Runtime client
            aws_kwargs = {
                'service_name': 'bedrock-runtime',
                'region_name': self.region
            }
            
            aws_key = os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if aws_key and aws_secret:
                aws_kwargs['aws_access_key_id'] = aws_key
                aws_kwargs['aws_secret_access_key'] = aws_secret
            
            self.client = boto3.client(**aws_kwargs)
            print(f"✓ Guardrails initialized: {len(self.guardrails)} guardrail(s) configured")
        else:
            self.client = None
            if self.enabled:
                print("⚠ Guardrails enabled but no IDs configured")
    
    def evaluate(self, prompt: str, response: str = None) -> Dict[str, Any]:
        """Evaluate prompt and/or response using all configured guardrails"""
        
        if not self.enabled or not self.guardrails:
            return {
                'enabled': False,
                'results': []
            }
        
        results = []
        
        for guardrail in self.guardrails:
            # Evaluate input prompt
            if self.mode in ['input_only', 'both']:
                input_result = self._evaluate_content(
                    content=prompt,
                    content_type='input',
                    guardrail_id=guardrail['id'],
                    guardrail_version=guardrail['version']
                )
                results.append(input_result)
            
            # Evaluate output response
            if response and self.mode in ['output_only', 'both']:
                output_result = self._evaluate_content(
                    content=response,
                    content_type='output',
                    guardrail_id=guardrail['id'],
                    guardrail_version=guardrail['version']
                )
                results.append(output_result)
        
        # Calculate overall status
        blocked_count = sum(1 for r in results if r['action'] == 'GUARDRAIL_INTERVENED')
        overall_status = 'BLOCKED' if blocked_count > 0 else 'PASSED'
        
        return {
            'enabled': True,
            'overall_status': overall_status,
            'total_evaluations': len(results),
            'blocked_count': blocked_count,
            'passed_count': len(results) - blocked_count,
            'results': results
        }
    
    def _evaluate_content(
        self, 
        content: str, 
        content_type: str,
        guardrail_id: str,
        guardrail_version: str
    ) -> Dict[str, Any]:
        """Evaluate a single piece of content with a specific guardrail"""
        
        try:
            # Prepare request based on content type
            if content_type == 'input':
                request = {
                    'guardrailIdentifier': guardrail_id,
                    'guardrailVersion': guardrail_version,
                    'source': 'INPUT',
                    'content': [
                        {
                            'text': {
                                'text': content
                            }
                        }
                    ]
                }
            else:  # output
                request = {
                    'guardrailIdentifier': guardrail_id,
                    'guardrailVersion': guardrail_version,
                    'source': 'OUTPUT',
                    'content': [
                        {
                            'text': {
                                'text': content
                            }
                        }
                    ]
                }
            
            # Call guardrail API
            response = self.client.apply_guardrail(**request)
            
            # Extract assessment details
            assessments = response.get('assessments', [])
            outputs = response.get('outputs', [])
            
            # Parse policy assessments
            policy_violations = []
            sensitive_info = []
            word_policy_violations = []
            content_policy_violations = []
            
            for assessment in assessments:
                # Topic policy
                if 'topicPolicy' in assessment:
                    for topic in assessment['topicPolicy'].get('topics', []):
                        if topic.get('action') == 'BLOCKED':
                            policy_violations.append({
                                'type': 'TOPIC_POLICY',
                                'name': topic.get('name', 'Unknown'),
                                'action': topic.get('action'),
                                'confidence': topic.get('confidence', 'UNKNOWN')
                            })
                
                # Content policy
                if 'contentPolicy' in assessment:
                    for filter_item in assessment['contentPolicy'].get('filters', []):
                        if filter_item.get('action') == 'BLOCKED':
                            content_policy_violations.append({
                                'type': 'CONTENT_POLICY',
                                'filter_type': filter_item.get('type', 'Unknown'),
                                'action': filter_item.get('action'),
                                'confidence': filter_item.get('confidence', 'UNKNOWN')
                            })
                
                # Word policy
                if 'wordPolicy' in assessment:
                    for word in assessment['wordPolicy'].get('customWords', []):
                        if word.get('action') == 'BLOCKED':
                            word_policy_violations.append({
                                'type': 'WORD_POLICY',
                                'match': word.get('match', 'Unknown'),
                                'action': word.get('action')
                            })
                    
                    for word in assessment['wordPolicy'].get('managedWordLists', []):
                        if word.get('action') == 'BLOCKED':
                            word_policy_violations.append({
                                'type': 'MANAGED_WORD_POLICY',
                                'match': word.get('match', 'Unknown'),
                                'list_type': word.get('type', 'Unknown'),
                                'action': word.get('action')
                            })
                
                # Sensitive information policy
                if 'sensitiveInformationPolicy' in assessment:
                    for pii in assessment['sensitiveInformationPolicy'].get('piiEntities', []):
                        if pii.get('action') == 'BLOCKED':
                            sensitive_info.append({
                                'type': 'PII',
                                'entity_type': pii.get('type', 'Unknown'),
                                'action': pii.get('action'),
                                'match': pii.get('match', 'Redacted')
                            })
                    
                    for regex in assessment['sensitiveInformationPolicy'].get('regexes', []):
                        if regex.get('action') == 'BLOCKED':
                            sensitive_info.append({
                                'type': 'REGEX',
                                'name': regex.get('name', 'Unknown'),
                                'action': regex.get('action'),
                                'match': regex.get('match', 'Redacted')
                            })
            
            # Determine action
            action = response.get('action', 'NONE')
            
            # Get filtered output if available
            filtered_output = None
            if outputs:
                filtered_output = outputs[0].get('text', content)
            
            return {
                'guardrail_id': guardrail_id,
                'guardrail_version': guardrail_version,
                'content_type': content_type,
                'action': action,
                'status': 'BLOCKED' if action == 'GUARDRAIL_INTERVENED' else 'PASSED',
                'usage': response.get('usage', {}),
                'policy_violations': policy_violations,
                'content_policy_violations': content_policy_violations,
                'word_policy_violations': word_policy_violations,
                'sensitive_info': sensitive_info,
                'filtered_output': filtered_output,
                'raw_assessments': assessments,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': True
            }
            
        except Exception as e:
            error_message = str(e)
            print(f"✗ Guardrail evaluation failed: {error_message}")
            
            return {
                'guardrail_id': guardrail_id,
                'guardrail_version': guardrail_version,
                'content_type': content_type,
                'action': 'ERROR',
                'status': 'ERROR',
                'error': error_message,
                'policy_violations': [],
                'content_policy_violations': [],
                'word_policy_violations': [],
                'sensitive_info': [],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'success': False
            }
    
    def format_trace(self, result: Dict[str, Any]) -> str:
        """Format guardrail result as a readable trace"""
        
        if not result.get('success'):
            return f"ERROR: {result.get('error', 'Unknown error')}"
        
        lines = []
        lines.append(f"Guardrail: {result['guardrail_id']} (v{result['guardrail_version']})")
        lines.append(f"Content Type: {result['content_type'].upper()}")
        lines.append(f"Action: {result['action']}")
        lines.append(f"Status: {result['status']}")
        
        # Add violations if any
        if result['policy_violations']:
            lines.append(f"\nTopic Policy Violations: {len(result['policy_violations'])}")
            for violation in result['policy_violations']:
                lines.append(f"  - {violation['name']} ({violation['confidence']})")
        
        if result['content_policy_violations']:
            lines.append(f"\nContent Policy Violations: {len(result['content_policy_violations'])}")
            for violation in result['content_policy_violations']:
                lines.append(f"  - {violation['filter_type']} ({violation['confidence']})")
        
        if result['word_policy_violations']:
            lines.append(f"\nWord Policy Violations: {len(result['word_policy_violations'])}")
            for violation in result['word_policy_violations'][:5]:  # Limit to 5
                lines.append(f"  - {violation['match']}")
        
        if result['sensitive_info']:
            lines.append(f"\nSensitive Information: {len(result['sensitive_info'])}")
            for info in result['sensitive_info'][:5]:  # Limit to 5
                lines.append(f"  - {info['entity_type']}: {info.get('match', 'Redacted')}")
        
        return '\n'.join(lines)
