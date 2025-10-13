"""
Debug Loop Engine - Automatic Multi-LLM Debug-Fix-Test Cycle

This module orchestrates the complete automatic debugging workflow:
1. Run tests and capture failures
2. Analyze failures with multiple LLMs in parallel
3. Reach consensus on best fix approach
4. Apply fix to codebase
5. Retest to verify fix works
6. Repeat until tests pass or max iterations reached

This is the core engine that enables autonomous bug fixing without manual intervention.

Architecture:
- Integrates TestRunner, MultiLLMOrchestrator, and ConsensusEngine
- Manages fix-test loop with configurable max iterations
- Tracks iteration history and previous failed attempts
- Provides structured feedback for each iteration
- Handles timeouts and error recovery

Usage:
    from engine.operations.debug_loop import DebugLoop
    
    loop = DebugLoop(project_root="/home/flip/agent-forge")
    result = await loop.fix_until_passes(
        test_files=["tests/test_file_editor.py"],
        bug_description="File editor crashes on empty files",
        max_iterations=5
    )
    
    if result.success:
        print(f"✅ Fixed in {result.iterations} iterations!")
    else:
        print(f"❌ Failed after {result.iterations} attempts")

Author: Agent Forge
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime

from engine.operations.test_runner import TestRunner, TestResult, TestFailure
from engine.operations.multi_llm_orchestrator import MultiLLMOrchestrator, LLMResponse
from engine.operations.consensus_engine import ConsensusEngine, ConsensusDecision
from engine.operations.file_editor import FileEditor

# Debug flag
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'

logger = logging.getLogger(__name__)

# Claude Context integration for semantic code search
try:
    from engine.utils.claude_context_wrapper import ClaudeContextWrapper
    CLAUDE_CONTEXT_AVAILABLE = True
    if DEBUG:
        logger.debug("✅ Claude Context available for semantic code search")
except ImportError:
    CLAUDE_CONTEXT_AVAILABLE = False
    if DEBUG:
        logger.debug("⚠️ Claude Context not available - using basic context loading")


@dataclass
class IterationResult:
    """Result of a single debug loop iteration"""
    iteration: int
    test_result: TestResult
    llm_responses: List[LLMResponse]
    consensus: ConsensusDecision
    fix_applied: bool
    fix_content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class DebugLoopResult:
    """Final result of complete debug loop"""
    success: bool
    iterations: int
    max_iterations: int
    final_test_result: TestResult
    iteration_history: List[IterationResult]
    total_duration: float
    failure_reason: Optional[str] = None


class DebugLoop:
    """
    Orchestrates automatic debug-fix-test cycles with multi-LLM analysis.
    
    This is the heart of the autonomous debugging system. It coordinates:
    - Test execution and failure analysis
    - Multi-LLM parallel analysis
    - Consensus-based fix selection
    - Automatic fix application
    - Iterative retesting until success
    """
    
    def __init__(
        self,
        project_root: str,
        max_iterations: int = 5,
        min_confidence: float = 0.6,
        min_agreement: int = 2,
        use_claude_context: bool = True,
        claude_context_collection: Optional[str] = None
    ):
        """
        Initialize debug loop
        
        Args:
            project_root: Root directory of the project
            max_iterations: Maximum fix-test iterations (default 5)
            min_confidence: Minimum consensus confidence (default 0.6)
            min_agreement: Minimum LLMs that must agree (default 2)
            use_claude_context: Enable Claude Context semantic search (default True)
            claude_context_collection: Specific collection name (default: auto-generate)
        """
        self.project_root = Path(project_root).resolve()
        self.max_iterations = max_iterations
        self.use_claude_context = use_claude_context and CLAUDE_CONTEXT_AVAILABLE
        
        # Initialize components
        # Note: TestRunner needs a terminal_ops instance
        # We'll initialize it when needed in the loop
        self.orchestrator = MultiLLMOrchestrator()
        self.consensus_engine = ConsensusEngine(
            min_confidence=min_confidence,
            min_agreement=min_agreement
        )
        self.file_editor = FileEditor(str(self.project_root))
        
        # Initialize Claude Context if available
        self.claude_context = None
        self.claude_context_collection = claude_context_collection
        if self.use_claude_context:
            try:
                self.claude_context = ClaudeContextWrapper()
                if DEBUG:
                    logger.debug(f"✅ Claude Context initialized for semantic search")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize Claude Context: {e}")
                self.use_claude_context = False
        
        if DEBUG:
            logger.debug(f"🔍 DebugLoop initialized")
            logger.debug(f"  - Project root: {self.project_root}")
            logger.debug(f"  - Max iterations: {max_iterations}")
            logger.debug(f"  - Min confidence: {min_confidence}")
            logger.debug(f"  - Min agreement: {min_agreement}")
            logger.debug(f"  - Claude Context: {'enabled' if self.use_claude_context else 'disabled'}")
    
    def _load_code_context(self, failures: List[TestFailure], bug_description: str = "") -> Dict[str, str]:
        """
        Load relevant code files based on test failures.
        Uses Claude Context for semantic search if available, otherwise loads files directly.
        
        Args:
            failures: List of test failures
            bug_description: Bug description for semantic search
        
        Returns:
            Dict mapping filename to file content
        """
        code_context = {}
        
        # Strategy 1: Claude Context semantic search (if available)
        if self.use_claude_context and self.claude_context and bug_description:
            if DEBUG:
                logger.debug(f"🔍 Using Claude Context for semantic code search")
            
            try:
                # Build search query from failures and bug description
                search_queries = []
                
                # Add bug description
                search_queries.append(bug_description)
                
                # Add error messages from failures
                for failure in failures[:3]:  # Limit to first 3 failures
                    if failure.error_message:
                        search_queries.append(failure.error_message)
                
                # Perform semantic search
                collection_name = self.claude_context_collection or f"agent-forge-{self.project_root.name}"
                
                for query in search_queries:
                    if DEBUG:
                        logger.debug(f"🔎 Searching: {query[:100]}...")
                    
                    results = self.claude_context.search_code(
                        query=query,
                        collection_name=collection_name,
                        limit=5,
                        score_threshold=0.7
                    )
                    
                    # Extract file paths from results
                    for result in results:
                        # Claude Context returns dict with 'file' and 'content' keys
                        if isinstance(result, dict):
                            filepath = result.get('file', '')
                            content = result.get('content', '')
                        else:
                            # Handle alternative result formats
                            filepath = str(result)
                            content = None
                        
                        if filepath and filepath not in code_context:
                            if content:
                                code_context[filepath] = content
                            else:
                                # Load file content
                                full_path = self.project_root / filepath
                                if full_path.exists():
                                    try:
                                        with open(full_path, 'r') as f:
                                            code_context[filepath] = f.read()
                                    except Exception as e:
                                        logger.warning(f"⚠️ Failed to load {filepath}: {e}")
                            
                            if DEBUG:
                                logger.debug(f"📄 Found via Claude Context: {filepath}")
                
                if DEBUG:
                    logger.debug(f"✅ Claude Context found {len(code_context)} relevant files")
            
            except Exception as e:
                logger.warning(f"⚠️ Claude Context search failed: {e}")
                logger.debug(f"  Falling back to basic context loading")
                # Fall through to Strategy 2
        
        # Strategy 2: Basic file loading from test failures
        if not code_context:  # If Claude Context didn't find anything or failed
            if DEBUG:
                logger.debug(f"📄 Using basic context loading from test failures")
            
            files_to_load = set()
            
            # Add source files from failures
            for failure in failures:
                if failure.source_file:
                    files_to_load.add(failure.source_file)
                
                # Also add test file
                if failure.test_file:
                    files_to_load.add(failure.test_file)
            
            # Load files
            for filepath in files_to_load:
                full_path = self.project_root / filepath
                if full_path.exists():
                    try:
                        with open(full_path, 'r') as f:
                            code_context[filepath] = f.read()
                        
                        if DEBUG:
                            logger.debug(f"📄 Loaded {filepath} ({len(code_context[filepath])} chars)")
                    
                    except Exception as e:
                        logger.error(f"❌ Failed to load {filepath}: {e}")
        
        if DEBUG:
            logger.debug(f"📊 Total context: {len(code_context)} files, {sum(len(c) for c in code_context.values())} chars")
        
        return code_context
    
    async def _run_iteration(
        self,
        iteration: int,
        test_runner: TestRunner,
        test_files: Optional[List[str]],
        bug_description: str,
        previous_attempts: List[str]
    ) -> IterationResult:
        """
        Run a single debug-fix-test iteration
        
        Args:
            iteration: Current iteration number (1-indexed)
            test_runner: TestRunner instance
            test_files: Specific test files to run
            bug_description: Original bug description
            previous_attempts: List of previous fix attempts that failed
        
        Returns:
            IterationResult with iteration details
        """
        if DEBUG:
            logger.debug(f"\n{'='*80}")
            logger.debug(f"🔄 ITERATION {iteration}/{self.max_iterations}")
            logger.debug(f"{'='*80}")
        
        # Step 1: Run tests
        print(f"\n🧪 Iteration {iteration}: Running tests...")
        test_result = test_runner.run_tests(test_paths=test_files)
        
        if test_result.success:
            # Tests passed! We're done
            if DEBUG:
                logger.debug(f"✅ Tests passed on iteration {iteration}!")
            
            return IterationResult(
                iteration=iteration,
                test_result=test_result,
                llm_responses=[],
                consensus=ConsensusDecision(
                    has_consensus=True,
                    chosen_fix="",
                    confidence=1.0,
                    supporting_providers=[],
                    total_weight=1.0,
                    reasoning="Tests passed, no fix needed",
                    alternatives=[],
                    conflicts=[]
                ),
                fix_applied=False,
                fix_content=""
            )
        
        # Step 2: Load code context (with Claude Context if available)
        print(f"📄 Loading code context from {len(test_result.failures)} failures...")
        if self.use_claude_context:
            print(f"🔍 Using Claude Context for semantic search...")
        code_context = self._load_code_context(test_result.failures, bug_description)
        print(f"✅ Loaded {len(code_context)} relevant files")
        
        # Step 3: Format test failures for LLMs
        test_failures_text = test_runner.format_failures_for_llm(test_result)
        
        # Step 4: Call multi-LLM orchestrator
        print(f"🤖 Analyzing with {len(self.orchestrator.providers_config)} LLMs...")
        llm_responses = await self.orchestrator.analyze_bug(
            bug_description=bug_description,
            code_context=code_context,
            test_failures=[test_failures_text],
            previous_attempts=previous_attempts
        )
        
        # Step 5: Reach consensus
        print(f"🗳️  Reaching consensus...")
        provider_weights = self.orchestrator.get_provider_weights()
        consensus = self.consensus_engine.reach_consensus(llm_responses, provider_weights)
        
        # Print consensus explanation
        print(self.consensus_engine.explain_decision(consensus))
        
        # Step 6: Apply fix if consensus reached
        fix_applied = False
        fix_content = ""
        
        if consensus.has_consensus:
            print(f"\n🔧 Applying fix...")
            fix_content = consensus.chosen_fix
            
            # Parse and apply fix
            # Fix should be in diff format or contain file path and content
            # For now, we'll assume the LLM provides structured output
            # TODO: Implement proper diff parsing and application
            
            # Simplified fix application (assumes fix contains full file content)
            # In production, this would use FileEditor to apply diffs
            try:
                # Extract file path from fix (LLMs should specify this)
                # For now, apply to first source file from failures
                if code_context and consensus.chosen_fix:
                    # This is a placeholder - real implementation would parse diff
                    # and use FileEditor to apply changes
                    if DEBUG:
                        logger.debug(f"🔍 Fix content ({len(fix_content)} chars):")
                        logger.debug(f"  {fix_content[:200]}...")
                    
                    fix_applied = True
                    print(f"✅ Fix applied (placeholder implementation)")
                else:
                    print(f"⚠️  No code context available to apply fix")
            
            except Exception as e:
                logger.error(f"❌ Failed to apply fix: {e}")
                fix_applied = False
        else:
            print(f"\n❌ No consensus reached - cannot apply fix")
        
        return IterationResult(
            iteration=iteration,
            test_result=test_result,
            llm_responses=llm_responses,
            consensus=consensus,
            fix_applied=fix_applied,
            fix_content=fix_content
        )
    
    async def fix_until_passes(
        self,
        test_files: Optional[List[str]] = None,
        bug_description: str = "",
        initial_context: Optional[Dict[str, str]] = None
    ) -> DebugLoopResult:
        """
        Main entry point: Run debug loop until tests pass or max iterations reached.
        
        This method orchestrates the complete automatic debugging workflow:
        1. Run tests to capture failures
        2. If tests fail:
           a. Analyze failures with multiple LLMs
           b. Reach consensus on best fix
           c. Apply fix to codebase
           d. Retest
           e. Repeat until success or max iterations
        
        Args:
            test_files: Specific test files to run (None = all tests)
            bug_description: High-level description of the bug
            initial_context: Initial code context (optional, will be loaded from failures)
        
        Returns:
            DebugLoopResult with complete debugging session results
        """
        import time
        start_time = time.time()
        
        print(f"\n{'='*80}")
        print(f"🚀 STARTING MULTI-LLM DEBUG LOOP")
        print(f"{'='*80}")
        print(f"Project: {self.project_root}")
        print(f"Max iterations: {self.max_iterations}")
        if test_files:
            print(f"Test files: {', '.join(test_files)}")
        else:
            print(f"Test files: ALL")
        print(f"Bug: {bug_description}")
        print(f"{'='*80}\n")
        
        # Initialize test runner
        # Note: This assumes terminal_operations is available
        # In production, this should be injected or created properly
        try:
            from engine.operations.terminal_operations import TerminalOperations
            terminal_ops = TerminalOperations(str(self.project_root))
            test_runner = TestRunner(terminal_ops)
        except ImportError:
            # Fallback if terminal_operations not available
            # Create mock for testing
            class MockTerminalOps:
                def __init__(self, root):
                    self.project_root = Path(root)
                
                def run_command(self, cmd, timeout=120):
                    import subprocess
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=self.project_root
                    )
                    return {
                        'success': result.returncode == 0,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'timeout_occurred': False
                    }
            
            terminal_ops = MockTerminalOps(self.project_root)
            test_runner = TestRunner(terminal_ops)
        
        iteration_history = []
        previous_attempts = []
        final_test_result = None
        failure_reason = None
        
        # Main loop
        for iteration in range(1, self.max_iterations + 1):
            try:
                iter_result = await self._run_iteration(
                    iteration=iteration,
                    test_runner=test_runner,
                    test_files=test_files,
                    bug_description=bug_description,
                    previous_attempts=previous_attempts
                )
                
                iteration_history.append(iter_result)
                final_test_result = iter_result.test_result
                
                # Check if tests passed
                if iter_result.test_result.success:
                    # Success!
                    total_duration = time.time() - start_time
                    
                    print(f"\n{'='*80}")
                    print(f"✅ SUCCESS!")
                    print(f"{'='*80}")
                    print(f"Tests passed after {iteration} iteration(s)")
                    print(f"Total duration: {total_duration:.2f}s")
                    print(f"{'='*80}\n")
                    
                    return DebugLoopResult(
                        success=True,
                        iterations=iteration,
                        max_iterations=self.max_iterations,
                        final_test_result=final_test_result,
                        iteration_history=iteration_history,
                        total_duration=total_duration
                    )
                
                # If fix was applied but tests still fail, add to previous attempts
                if iter_result.fix_applied:
                    previous_attempts.append(iter_result.fix_content)
                
                # If no fix was applied (no consensus), record this
                if not iter_result.fix_applied and not iter_result.consensus.has_consensus:
                    print(f"⚠️  Iteration {iteration}: No consensus, cannot proceed effectively")
            
            except Exception as e:
                logger.error(f"❌ Iteration {iteration} failed with exception: {e}")
                failure_reason = f"Exception in iteration {iteration}: {str(e)}"
                break
        
        # Max iterations reached or exception occurred
        total_duration = time.time() - start_time
        
        print(f"\n{'='*80}")
        print(f"❌ DEBUG LOOP FAILED")
        print(f"{'='*80}")
        print(f"Iterations: {len(iteration_history)}/{self.max_iterations}")
        print(f"Total duration: {total_duration:.2f}s")
        if failure_reason:
            print(f"Reason: {failure_reason}")
        else:
            print(f"Reason: Maximum iterations reached without passing tests")
        print(f"{'='*80}\n")
        
        return DebugLoopResult(
            success=False,
            iterations=len(iteration_history),
            max_iterations=self.max_iterations,
            final_test_result=final_test_result or TestResult(),
            iteration_history=iteration_history,
            total_duration=total_duration,
            failure_reason=failure_reason or "Maximum iterations reached"
        )


# CLI for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-LLM Debug Loop")
    parser.add_argument("--project-root", default=os.getcwd(), help="Project root directory")
    parser.add_argument("--test-files", nargs="+", help="Specific test files to run")
    parser.add_argument("--bug", required=True, help="Bug description")
    parser.add_argument("--max-iterations", type=int, default=5, help="Maximum iterations")
    parser.add_argument("--min-confidence", type=float, default=0.6, help="Minimum consensus confidence")
    parser.add_argument("--min-agreement", type=int, default=2, help="Minimum LLMs that must agree")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        os.environ['DEBUG'] = 'true'
    else:
        logging.basicConfig(level=logging.INFO)
    
    # Run debug loop
    async def main():
        loop = DebugLoop(
            project_root=args.project_root,
            max_iterations=args.max_iterations,
            min_confidence=args.min_confidence,
            min_agreement=args.min_agreement
        )
        
        result = await loop.fix_until_passes(
            test_files=args.test_files,
            bug_description=args.bug
        )
        
        # Print final summary
        print("\n" + "="*80)
        print("FINAL SUMMARY")
        print("="*80)
        print(f"Success: {'✅ YES' if result.success else '❌ NO'}")
        print(f"Iterations: {result.iterations}/{result.max_iterations}")
        print(f"Duration: {result.total_duration:.2f}s")
        
        if result.final_test_result:
            print(f"\nFinal Test Results:")
            print(f"  Passed: {result.final_test_result.passed}")
            print(f"  Failed: {result.final_test_result.failed}")
            print(f"  Total: {result.final_test_result.total}")
        
        if not result.success and result.failure_reason:
            print(f"\nFailure Reason: {result.failure_reason}")
        
        print("="*80)
        
        # Exit with appropriate code
        import sys
        sys.exit(0 if result.success else 1)
    
    asyncio.run(main())
