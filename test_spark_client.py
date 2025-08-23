#!/usr/bin/env python3
"""Test Spark client directly"""

import asyncio
import json
from automagik_tools.tools.spark.config import SparkConfig
from automagik_tools.tools.spark.client import SparkClient


async def test_workflow_execution():
    """Test running a workflow"""
    config = SparkConfig()
    client = SparkClient(config)
    
    # Get workflow details
    workflow_id = "f9c38d51-56a4-42e8-8b0f-10b180345468"
    
    print("Getting workflow details...")
    workflow = await client.get_workflow(workflow_id)
    print(f"Workflow: {workflow['name']}")
    print(f"Type: {workflow['data']['type']}")
    
    # Try to run the workflow
    print("\nRunning workflow with input: 'Write a simple hello world function in Python'")
    result = await client.run_workflow(
        workflow_id=workflow_id,
        input_data="Write a simple hello world function in Python"
    )
    
    print(f"\nResult: {json.dumps(result, indent=2)}")
    
    # If we got a task ID, wait a bit and check the result
    if result.get("id") and result.get("status") != "failed":
        task_id = result["id"]
        print(f"\nTask created: {task_id}")
        
        # Wait a bit for processing
        await asyncio.sleep(5)
        
        # Get task details
        task = await client.get_task(task_id)
        print(f"\nTask status: {task['status']}")
        if task.get("output_data"):
            print(f"Output: {task['output_data']}")


if __name__ == "__main__":
    asyncio.run(test_workflow_execution())