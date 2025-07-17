"""
Progress tracking for Automagik Workflows V2 with FastMCP integration
"""

import asyncio
import logging
from typing import Optional, Callable, Any
from datetime import datetime, timedelta

from fastmcp import Context

from .client import AutomagikWorkflowsClient
from .models import WorkflowStatus, WorkflowStatusResponse

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks workflow progress with real-time streaming via FastMCP Context."""
    
    def __init__(self, client: AutomagikWorkflowsClient, polling_interval: int = 8):
        self.client = client
        self.polling_interval = polling_interval
        self._tracking_tasks = {}
        self._last_status = {}
    
    async def track_workflow_progress(
        self,
        run_id: str,
        ctx: Context,
        on_completion: Optional[Callable[[WorkflowStatusResponse], Any]] = None,
        timeout_minutes: Optional[int] = None
    ) -> WorkflowStatusResponse:
        """Track workflow progress with real-time updates via FastMCP Context."""
        
        start_time = datetime.now()
        timeout_delta = timedelta(minutes=timeout_minutes) if timeout_minutes else None
        
        try:
            await ctx.report_progress(0, 1, f"Starting progress tracking for workflow {run_id}")
            
            while True:
                # Check for timeout
                if timeout_delta and (datetime.now() - start_time) > timeout_delta:
                    await ctx.report_progress(1, 1, f"Timeout reached for workflow {run_id}")
                    break
                
                try:
                    # Get current status
                    status = await self.client.get_workflow_status(run_id, detailed=True)
                    
                    # Report progress if we have turn information
                    if status.current_turn is not None and status.max_turns is not None:
                        progress_message = self._format_progress_message(status)
                        await ctx.report_progress(
                            progress=status.current_turn,
                            total=status.max_turns,
                            message=progress_message
                        )
                    else:
                        # Fallback progress reporting
                        progress_message = self._format_status_message(status)
                        await ctx.report_progress(0, 1, progress_message)
                    
                    # Cache the status for comparison
                    self._last_status[run_id] = status
                    
                    # Check if workflow is complete
                    if status.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
                        final_message = self._format_completion_message(status)
                        
                        if status.status == WorkflowStatus.COMPLETED:
                            await ctx.report_progress(
                                progress=status.max_turns or 1,
                                total=status.max_turns or 1,
                                message=final_message
                            )
                        else:
                            await ctx.report_progress(0, 1, final_message)
                        
                        # Call completion callback if provided
                        if on_completion:
                            try:
                                await on_completion(status)
                            except Exception as e:
                                logger.error(f"Error in completion callback: {e}")
                        
                        return status
                    
                    # Wait before next poll
                    await asyncio.sleep(self.polling_interval)
                    
                except Exception as e:
                    logger.error(f"Error checking workflow status: {e}")
                    await ctx.report_progress(0, 1, f"Error checking status: {str(e)[:100]}")
                    
                    # Continue polling unless it's a critical error
                    if "not found" in str(e).lower():
                        break
                    
                    await asyncio.sleep(self.polling_interval)
            
            # If we exit the loop without completion, get final status
            try:
                final_status = await self.client.get_workflow_status(run_id, detailed=True)
                return final_status
            except Exception as e:
                logger.error(f"Failed to get final status: {e}")
                raise
                
        except Exception as e:
            await ctx.report_progress(0, 1, f"Progress tracking failed: {str(e)[:100]}")
            raise
        finally:
            # Clean up tracking record
            self._last_status.pop(run_id, None)
    
    def _format_progress_message(self, status: WorkflowStatusResponse) -> str:
        """Format progress message for Context.report_progress."""
        base_msg = f"Turn {status.current_turn}/{status.max_turns}"
        
        if status.current_action:
            base_msg += f": {status.current_action}"
        else:
            base_msg += f" - {status.status.value.title()}"
        
        # Add workspace info if available
        if status.workspace_path:
            base_msg += f" (workspace: {status.workspace_path.split('/')[-1]})"
        
        return base_msg
    
    def _format_status_message(self, status: WorkflowStatusResponse) -> str:
        """Format status message when turn info is not available."""
        base_msg = f"Workflow {status.status.value.title()}"
        
        if status.current_action:
            base_msg += f": {status.current_action}"
        
        # Add timing info
        if status.started_at:
            elapsed = datetime.now() - status.started_at
            base_msg += f" (running {elapsed.seconds//60}m {elapsed.seconds%60}s)"
        
        return base_msg
    
    def _format_completion_message(self, status: WorkflowStatusResponse) -> str:
        """Format completion message."""
        if status.status == WorkflowStatus.COMPLETED:
            msg = "✅ Workflow completed successfully"
        elif status.status == WorkflowStatus.FAILED:
            msg = "❌ Workflow failed"
            if status.error_message:
                msg += f": {status.error_message[:100]}"
        elif status.status == WorkflowStatus.CANCELLED:
            msg = "🛑 Workflow cancelled"
        else:
            msg = f"Workflow finished with status: {status.status.value}"
        
        # Add timing info
        if status.started_at:
            if status.completed_at:
                duration = status.completed_at - status.started_at
            else:
                duration = datetime.now() - status.started_at
            
            msg += f" (duration: {duration.seconds//60}m {duration.seconds%60}s)"
        
        return msg
    
    async def start_background_tracking(self, run_id: str, ctx: Context) -> None:
        """Start background progress tracking (fire-and-forget)."""
        if run_id in self._tracking_tasks:
            logger.warning(f"Already tracking workflow {run_id}")
            return
        
        task = asyncio.create_task(
            self.track_workflow_progress(run_id, ctx)
        )
        self._tracking_tasks[run_id] = task
        
        # Clean up task when done
        def cleanup_task(task):
            self._tracking_tasks.pop(run_id, None)
        
        task.add_done_callback(cleanup_task)
    
    async def stop_tracking(self, run_id: str) -> None:
        """Stop tracking a specific workflow."""
        task = self._tracking_tasks.pop(run_id, None)
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    
    async def stop_all_tracking(self) -> None:
        """Stop all active tracking tasks."""
        tasks = list(self._tracking_tasks.values())
        self._tracking_tasks.clear()
        
        for task in tasks:
            if not task.done():
                task.cancel()
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_last_status(self, run_id: str) -> Optional[WorkflowStatusResponse]:
        """Get the last known status for a workflow."""
        return self._last_status.get(run_id)
    
    def is_tracking(self, run_id: str) -> bool:
        """Check if a workflow is currently being tracked."""
        task = self._tracking_tasks.get(run_id)
        return task is not None and not task.done()
    
    def get_active_tracking_count(self) -> int:
        """Get count of actively tracked workflows."""
        return len([
            task for task in self._tracking_tasks.values()
            if not task.done()
        ])