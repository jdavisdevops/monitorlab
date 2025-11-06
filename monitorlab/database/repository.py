"""Repository for database operations."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from monitorlab.database.models import TestRun, TestResult, get_session


class TestRunRepository:
    """Repository for test run database operations."""

    @staticmethod
    async def create_test_run(
        name: str,
        description: Optional[str] = None,
        target_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TestRun:
        """Create a new test run.

        Args:
            name: Test run name
            description: Optional description
            target_url: Optional target URL
            metadata: Optional metadata dict

        Returns:
            Created TestRun instance
        """
        async with get_session() as session:
            test_run = TestRun(
                name=name,
                description=description,
                target_url=target_url,
                status="running",
                metadata=metadata or {},
            )
            session.add(test_run)
            await session.commit()
            await session.refresh(test_run)
            return test_run

    @staticmethod
    async def update_test_run(
        test_run_id: int,
        status: Optional[str] = None,
        completed_at: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
    ) -> TestRun:
        """Update a test run.

        Args:
            test_run_id: Test run ID
            status: New status
            completed_at: Completion timestamp
            duration_seconds: Duration in seconds

        Returns:
            Updated TestRun instance
        """
        async with get_session() as session:
            result = await session.execute(select(TestRun).where(TestRun.id == test_run_id))
            test_run = result.scalar_one()

            if status:
                test_run.status = status
            if completed_at:
                test_run.completed_at = completed_at
            if duration_seconds is not None:
                test_run.duration_seconds = duration_seconds

            await session.commit()
            await session.refresh(test_run)
            return test_run

    @staticmethod
    async def add_test_result(
        test_run_id: int,
        agent_name: str,
        agent_type: str,
        task: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        duration_seconds: Optional[float] = None,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        screenshot_path: Optional[str] = None,
    ) -> TestResult:
        """Add a test result to a run.

        Args:
            test_run_id: Test run ID
            agent_name: Agent name
            agent_type: Agent type
            task: Task description
            status: Result status
            started_at: Start timestamp
            completed_at: Completion timestamp
            duration_seconds: Duration in seconds
            output: Output data
            error: Error message if any
            screenshot_path: Path to screenshot if any

        Returns:
            Created TestResult instance
        """
        async with get_session() as session:
            test_result = TestResult(
                test_run_id=test_run_id,
                agent_name=agent_name,
                agent_type=agent_type,
                task=task,
                status=status,
                started_at=started_at,
                completed_at=completed_at,
                duration_seconds=duration_seconds,
                output=output or {},
                error=error,
                screenshot_path=screenshot_path,
            )
            session.add(test_result)
            await session.commit()
            await session.refresh(test_result)
            return test_result

    @staticmethod
    async def get_test_run(test_run_id: int, include_results: bool = True) -> Optional[TestRun]:
        """Get a test run by ID.

        Args:
            test_run_id: Test run ID
            include_results: Whether to include results

        Returns:
            TestRun instance or None
        """
        async with get_session() as session:
            query = select(TestRun).where(TestRun.id == test_run_id)

            if include_results:
                query = query.options(selectinload(TestRun.results))

            result = await session.execute(query)
            return result.scalar_one_or_none()

    @staticmethod
    async def get_recent_test_runs(limit: int = 10, include_results: bool = False) -> List[TestRun]:
        """Get recent test runs.

        Args:
            limit: Maximum number of runs to return
            include_results: Whether to include results

        Returns:
            List of TestRun instances
        """
        async with get_session() as session:
            query = (
                select(TestRun)
                .order_by(desc(TestRun.started_at))
                .limit(limit)
            )

            if include_results:
                query = query.options(selectinload(TestRun.results))

            result = await session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    async def get_test_runs_by_name(name: str, limit: int = 10) -> List[TestRun]:
        """Get test runs by name.

        Args:
            name: Test run name
            limit: Maximum number of runs to return

        Returns:
            List of TestRun instances
        """
        async with get_session() as session:
            query = (
                select(TestRun)
                .where(TestRun.name == name)
                .order_by(desc(TestRun.started_at))
                .limit(limit)
            )
            result = await session.execute(query)
            return list(result.scalars().all())

    @staticmethod
    async def get_test_statistics(test_run_id: int) -> Dict[str, Any]:
        """Get statistics for a test run.

        Args:
            test_run_id: Test run ID

        Returns:
            Dictionary with statistics
        """
        test_run = await TestRunRepository.get_test_run(test_run_id, include_results=True)

        if not test_run:
            return {}

        total = len(test_run.results)
        success = sum(1 for r in test_run.results if r.status == "success")
        failed = sum(1 for r in test_run.results if r.status == "failure")
        error = sum(1 for r in test_run.results if r.status == "error")

        return {
            "test_run_id": test_run_id,
            "name": test_run.name,
            "status": test_run.status,
            "total_agents": total,
            "success": success,
            "failed": failed,
            "error": error,
            "success_rate": f"{(success / total * 100):.1f}%" if total > 0 else "0%",
            "duration_seconds": test_run.duration_seconds,
            "started_at": test_run.started_at.isoformat(),
            "completed_at": test_run.completed_at.isoformat() if test_run.completed_at else None,
        }
