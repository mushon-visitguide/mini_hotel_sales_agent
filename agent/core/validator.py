"""Result validation for adaptive feedback loop"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationIssue:
    """Represents an issue found during validation"""
    type: str  # 'error', 'no_availability', 'empty_result', 'unexpected_data'
    tool_id: str
    message: str
    severity: str  # 'critical', 'high', 'medium', 'low'


@dataclass
class ValidationResult:
    """Result of validating tool execution results"""
    needs_adaptation: bool
    issues: List[ValidationIssue]
    feedback: Optional[str]  # Natural language feedback for planner

    @property
    def is_valid(self) -> bool:
        """Check if results are valid (no adaptation needed)"""
        return not self.needs_adaptation

    @property
    def critical_issues(self) -> List[ValidationIssue]:
        """Get critical issues that require immediate adaptation"""
        return [i for i in self.issues if i.severity == 'critical']

    @property
    def has_errors(self) -> bool:
        """Check if there are any error-type issues"""
        return any(i.type == 'error' for i in self.issues)


class ResultValidator:
    """
    Analyzes tool results and decides if adaptation is needed.

    This is a key component of the hybrid feedback loop that checks if:
    - Tool executions succeeded
    - Results contain expected data
    - Results are useful for answering the user's request

    If issues are found, it generates feedback for the planner to adapt.
    """

    def __init__(self, adaptation_threshold: float = 0.5):
        """
        Initialize validator.

        Args:
            adaptation_threshold: Fraction of tools that must fail/be empty
                                 to trigger adaptation (0.0-1.0)
        """
        self.adaptation_threshold = adaptation_threshold

    async def analyze_results(
        self,
        user_message: str,
        plan_action: str,
        tools: List[Any],  # List of ToolCall objects
        results: Dict[str, Any]
    ) -> ValidationResult:
        """
        Analyze tool execution results and decide if adaptation is needed.

        Args:
            user_message: Original user request
            plan_action: The action the planner intended to take
            tools: List of tool calls that were executed
            results: Dict mapping tool_id to execution result

        Returns:
            ValidationResult with adaptation decision and feedback
        """
        issues = []

        # Check each tool's result
        for tool_call in tools:
            tool_id = tool_call.id
            tool_name = tool_call.tool
            result = results.get(tool_id)

            # Check for explicit errors
            if isinstance(result, dict) and "error" in result:
                issues.append(ValidationIssue(
                    type='error',
                    tool_id=tool_id,
                    message=f"{tool_name} failed: {result['error']}",
                    severity='critical'
                ))
                continue

            # Check for empty availability results
            if 'availability' in tool_name or 'get_rooms' in tool_name:
                if isinstance(result, dict):
                    rooms = result.get('available_rooms', [])
                    if not rooms or len(rooms) == 0:
                        issues.append(ValidationIssue(
                            type='no_availability',
                            tool_id=tool_id,
                            message='No rooms available for requested dates',
                            severity='high'
                        ))

            # Check for unexpectedly empty results
            if result is None or (isinstance(result, (list, dict, str)) and not result):
                issues.append(ValidationIssue(
                    type='empty_result',
                    tool_id=tool_id,
                    message=f'{tool_name} returned empty/null result',
                    severity='medium'
                ))

        # Decide if adaptation is needed based on issues
        needs_adaptation = self._should_adapt(issues, len(tools))

        # Generate feedback for planner if adaptation needed
        feedback = None
        if needs_adaptation:
            feedback = self._generate_feedback(user_message, plan_action, issues, results)

        logger.info(
            f"Validation complete: {len(issues)} issues, "
            f"adaptation_needed={needs_adaptation}"
        )

        return ValidationResult(
            needs_adaptation=needs_adaptation,
            issues=issues,
            feedback=feedback
        )

    def _should_adapt(self, issues: List[ValidationIssue], total_tools: int) -> bool:
        """
        Decide if adaptation is needed based on issues found.

        Adaptation is triggered if:
        - Any critical issues (errors)
        - High percentage of tools have issues
        - Specific patterns that commonly need adaptation
        """
        if not issues:
            return False

        # Always adapt on critical errors
        if any(i.severity == 'critical' for i in issues):
            return True

        # Adapt if high/critical issues exceed threshold
        high_severity_issues = [i for i in issues if i.severity in ('high', 'critical')]
        if len(high_severity_issues) / max(total_tools, 1) >= self.adaptation_threshold:
            return True

        # Specific patterns that need adaptation
        # - Multiple no_availability issues (suggests trying alternatives)
        no_availability_count = sum(1 for i in issues if i.type == 'no_availability')
        if no_availability_count >= 1:  # Even one no-availability should trigger adaptation
            return True

        return False

    def _generate_feedback(
        self,
        user_message: str,
        plan_action: str,
        issues: List[ValidationIssue],
        results: Dict[str, Any]
    ) -> str:
        """
        Generate natural language feedback for the planner.

        The feedback helps the planner understand what went wrong
        and suggests alternative approaches.
        """
        feedback_parts = [
            "## Validation Feedback",
            "",
            f"Original request: {user_message}",
            f"Attempted action: {plan_action}",
            "",
            "## Issues Found:",
        ]

        # Group issues by type
        errors = [i for i in issues if i.type == 'error']
        no_availability = [i for i in issues if i.type == 'no_availability']
        empty_results = [i for i in issues if i.type == 'empty_result']

        if errors:
            feedback_parts.append("\n**Errors:**")
            for issue in errors:
                feedback_parts.append(f"- {issue.message}")

        if no_availability:
            feedback_parts.append("\n**No Availability:**")
            for issue in no_availability:
                feedback_parts.append(f"- {issue.message}")

        if empty_results:
            feedback_parts.append("\n**Empty Results:**")
            for issue in empty_results:
                feedback_parts.append(f"- {issue.message}")

        # Generate suggestions based on issue types
        feedback_parts.append("\n## Suggestions for Adaptation:")

        if no_availability:
            feedback_parts.extend([
                "- Try nearby dates (±1-3 days)",
                "- Try shorter stay duration if request was for many nights",
                "- Check if there are alternative room types available",
                "- Consider suggesting the closest available dates to the user"
            ])

        if errors:
            feedback_parts.extend([
                "- Retry failed tools with adjusted parameters",
                "- Try alternative tools if available",
                "- Check if required dependencies are available"
            ])

        if empty_results:
            feedback_parts.extend([
                "- Verify tool parameters were correct",
                "- Try broadening search criteria",
                "- Check if the requested data exists"
            ])

        feedback_parts.append("\n## Available Results:")
        feedback_parts.append(self._summarize_successful_results(results, issues))

        return "\n".join(feedback_parts)

    def _summarize_successful_results(
        self,
        results: Dict[str, Any],
        issues: List[ValidationIssue]
    ) -> str:
        """Summarize successful tool results that can inform adaptation"""
        failed_tool_ids = {i.tool_id for i in issues}
        successful = {tid: r for tid, r in results.items() if tid not in failed_tool_ids}

        if not successful:
            return "No successful results to use for adaptation."

        summary_parts = []
        for tool_id, result in successful.items():
            if isinstance(result, dict):
                # Calendar results
                if "check_in" in result and "check_out" in result:
                    summary_parts.append(
                        f"- {tool_id}: Dates resolved to "
                        f"{result['check_in']} to {result['check_out']}"
                    )
                # Guest info
                elif "guest_name" in result:
                    summary_parts.append(f"- {tool_id}: Guest info retrieved")
                # Generic dict result
                else:
                    summary_parts.append(f"- {tool_id}: Success (data available)")
            elif isinstance(result, str):
                # Truncate long strings
                result_preview = result[:100] + "..." if len(result) > 100 else result
                summary_parts.append(f"- {tool_id}: {result_preview}")
            else:
                summary_parts.append(f"- {tool_id}: Success")

        return "\n".join(summary_parts) if summary_parts else "No detailed results available."
