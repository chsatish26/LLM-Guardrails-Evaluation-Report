"""
Simplified Evaluation Module with Guardrails
Focuses on guardrails evaluation with proper pass/fail logic
"""

import json
from datetime import datetime
from typing import Dict, Any, List


class SimplifiedEvaluator:
    """Simplified evaluator focusing on guardrails"""
    
    def __init__(self, test_client, guardrails, log_file: str):
        self.test_client = test_client
        self.guardrails = guardrails
        self.log_file = log_file
    
    def evaluate_test(self, prompt: str, template: Dict[str, Any], model_info: Dict) -> Dict[str, Any]:
        """Evaluate a single test case with guardrails"""
        
        # Get expected guardrail action from template
        expected_action = template.get('expected_guardrail_action', 'none').lower()
        # Expected values: 'block', 'none'
        
        # First, evaluate input with guardrails
        input_guardrails_result = self.guardrails.evaluate(prompt=prompt)
        
        # Check if input was blocked
        input_blocked = (
            input_guardrails_result.get('enabled') and 
            input_guardrails_result.get('overall_status') == 'BLOCKED'
        )
        
        # Invoke test model if input not blocked
        if input_blocked:
            response = "[BLOCKED BY INPUT GUARDRAILS]"
            llm_result = {
                'success': False,
                'response': response,
                'input_tokens': 0,
                'output_tokens': 0,
                'latency_ms': 0,
                'error': 'Input blocked by guardrails'
            }
            output_guardrails_result = {'enabled': False, 'results': []}
        else:
            llm_result = self.test_client.invoke(prompt)
            
            if llm_result['success']:
                response = llm_result['response']
                # Evaluate output with guardrails
                output_guardrails_result = self.guardrails.evaluate(
                    prompt=prompt,
                    response=response
                )
            else:
                response = ''
                output_guardrails_result = {'enabled': False, 'results': []}
        
        # Check if output was blocked
        output_blocked = (
            output_guardrails_result.get('enabled') and 
            output_guardrails_result.get('overall_status') == 'BLOCKED'
        )
        
        # Determine overall status based on expected guardrail action
        any_blocked = input_blocked or output_blocked
        
        if expected_action == 'block':
            # This test EXPECTS to be blocked by guardrails
            if any_blocked:
                status = 'PASSED'  # Correctly blocked as expected
                pass_reason = 'blocked_as_expected'
            elif not llm_result['success']:
                status = 'ERROR'  # Technical error
                pass_reason = None
            else:
                status = 'ERROR'  # Should have been blocked but wasn't
                pass_reason = None
        else:
            # This test expects normal execution (not blocked)
            if any_blocked:
                status = 'ERROR'  # Incorrectly blocked
                pass_reason = None
            elif not llm_result['success']:
                status = 'ERROR'  # Technical error
                pass_reason = None
            else:
                status = 'PASSED'  # Normal execution successful
                pass_reason = 'normal_pass'
        
        # Create result
        result = {
            'category': template.get('category', 'unknown'),
            'test_name': template.get('name', 'unknown'),
            'prompt': prompt,
            'response': response,
            'status': status,
            'pass_reason': pass_reason,  # 'blocked_as_expected', 'normal_pass', or None
            'expected_guardrail_action': expected_action,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'model_id': model_info['model_id'],
            'provider': model_info['provider'],
            'input_tokens': llm_result.get('input_tokens', 0),
            'output_tokens': llm_result.get('output_tokens', 0),
            'total_tokens': llm_result.get('input_tokens', 0) + llm_result.get('output_tokens', 0),
            'latency_ms': llm_result.get('latency_ms', 0),
            'guardrails_input': input_guardrails_result,
            'guardrails_output': output_guardrails_result,
            'was_blocked': any_blocked,
            'error': llm_result.get('error') if not llm_result.get('success') and not any_blocked else None
        }
        
        # Log result
        self._log_result(result)
        
        return result
    
    def _log_result(self, result: Dict[str, Any]):
        """Log evaluation result to file"""
        
        try:
            log_entry = {
                'timestamp': result['timestamp'],
                'test_name': result['test_name'],
                'model_id': result['model_id'],
                'provider': result['provider'],
                'status': result['status'],
                'expected_action': result['expected_guardrail_action'],
                'was_blocked': result['was_blocked'],
                'prompt': result['prompt'][:200] + '...' if len(result['prompt']) > 200 else result['prompt'],
                'response': result['response'][:200] + '...' if len(result['response']) > 200 else result['response']
            }
            
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            print(f"Warning: Could not write to log file: {e}")