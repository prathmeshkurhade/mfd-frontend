from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.database import supabase_admin as supabase
from app.models.task import TaskCreate, TaskUpdate


class TaskService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    async def list_tasks(
        self,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        client_id: Optional[UUID] = None,
        lead_id: Optional[UUID] = None,
        due_date: Optional[date] = None,
        sort_by: str = "due_date",
        sort_order: str = "asc",
    ) -> Dict[str, Any]:
        """List tasks with filters and pagination."""
        query = (
            supabase.table("tasks")
            .select("*", count="exact")
            .eq("user_id", str(self.user_id))
        )

        # Apply filters
        if status:
            query = query.eq("status", status)
        if priority:
            query = query.eq("priority", priority)
        if client_id:
            query = query.eq("client_id", str(client_id))
        if lead_id:
            query = query.eq("lead_id", str(lead_id))
        if due_date:
            query = query.eq("due_date", due_date.isoformat())

        # Apply sorting
        order_by = sort_by if sort_by else "due_date"
        ascending = sort_order.lower() == "asc"
        query = query.order(order_by, desc=not ascending)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        response = query.execute()
        tasks = response.data if response.data else []

        # Enrich with client/lead names if needed
        enriched_tasks = []
        for task in tasks:
            if task.get("client_id"):
                client = (
                    supabase.table("clients")
                    .select("name")
                    .eq("id", task["client_id"])
                    .limit(1)
                    .execute()
                )
                if client.data:
                    task["client_name"] = client.data[0].get("name")

            if task.get("lead_id"):
                lead = (
                    supabase.table("leads")
                    .select("name")
                    .eq("id", task["lead_id"])
                    .limit(1)
                    .execute()
                )
                if lead.data:
                    task["lead_name"] = lead.data[0].get("name")

            if "description" in task and "title" not in task:
                task["title"] = task["description"]

            enriched_tasks.append(task)

        total = response.count if hasattr(response, "count") else len(tasks)
        total_pages = (total + limit - 1) // limit if total > 0 else 0

        return {
            "tasks": enriched_tasks,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
        }

    async def create_task(self, data: TaskCreate) -> Dict[str, Any]:
        """Create a new task."""
        # Prepare insert data — mode="json" converts date/enum/UUID to strings
        insert_data = data.model_dump(mode="json", exclude_unset=True)
        insert_data["user_id"] = str(self.user_id)
        insert_data["original_date"] = insert_data.get("due_date")
        # Map title to description (database uses description)
        if "title" in insert_data:
            insert_data["description"] = insert_data.pop("title")

        # Convert enum and date values to JSON-serializable strings
        for key, value in list(insert_data.items()):
            if hasattr(value, "value"):
                insert_data[key] = value.value
            elif isinstance(value, (date, datetime)):
                insert_data[key] = value.isoformat()

        response = supabase.table("tasks").insert(insert_data).execute()
        if response.data:
            task = response.data[0]
            # Map description back to title for response
            if "description" in task:
                task["title"] = task["description"]
            return task
        raise Exception("Failed to create task")

    async def get_task(self, task_id: UUID) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        response = (
            supabase.table("tasks")
            .select("*")
            .eq("id", str(task_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            task = response.data[0]
            # Map description to title
            if "description" in task:
                task["title"] = task["description"]
            return task
        return None

    async def update_task(
        self, task_id: UUID, data: TaskUpdate
    ) -> Dict[str, Any]:
        """Update task."""
        # Get existing task
        existing = await self.get_task(task_id)
        if not existing:
            raise ValueError("Task not found")

        # Prepare update data — mode="json" converts date/enum/UUID to strings
        update_data = data.model_dump(mode="json", exclude_unset=True)

        # Map title to description
        if "title" in update_data:
            update_data["description"] = update_data.pop("title")

        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = (
            supabase.table("tasks")
            .update(update_data)
            .eq("id", str(task_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            task = response.data[0]
            # Map description back to title
            if "description" in task:
                task["title"] = task["description"]
            return task
        raise Exception("Failed to update task")

    async def delete_task(self, task_id: UUID) -> None:
        """Hard delete task."""
        response = (
            supabase.table("tasks")
            .delete()
            .eq("id", str(task_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if not response.data:
            raise ValueError("Task not found")

    async def complete_task(self, task_id: UUID) -> Dict[str, Any]:
        """Mark task as completed."""
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        response = (
            supabase.table("tasks")
            .update(update_data)
            .eq("id", str(task_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            task = response.data[0]
            if "description" in task:
                task["title"] = task["description"]
            return task
        raise ValueError("Task not found")

    async def carry_forward(
        self, task_id: UUID, new_date: date
    ) -> Dict[str, Any]:
        """Carry forward task to new date."""
        existing = await self.get_task(task_id)
        if not existing:
            raise ValueError("Task not found")

        # Get current carry_forward_count
        current_count = existing.get("carry_forward_count", 0)

        update_data = {
            "status": "carried_forward",
            "due_date": new_date.isoformat(),
            "carry_forward_count": current_count + 1,
            "updated_at": datetime.utcnow().isoformat(),
        }

        response = (
            supabase.table("tasks")
            .update(update_data)
            .eq("id", str(task_id))
            .eq("user_id", str(self.user_id))
            .execute()
        )
        if response.data:
            task = response.data[0]
            if "description" in task:
                task["title"] = task["description"]
            return task
        raise Exception("Failed to carry forward task")

    async def get_today_tasks(self) -> Dict[str, Any]:
        """Get tasks with due_date = today, split by status."""
        today = date.today().isoformat()
        response = (
            supabase.table("tasks")
            .select("*")
            .eq("user_id", str(self.user_id))
            .eq("due_date", today)
            .execute()
        )
        tasks = response.data if response.data else []

        # Map description to title and split by status
        pending = []
        completed = []
        overdue = []

        for task in tasks:
            if "description" in task:
                task["title"] = task["description"]

            status = task.get("status", "pending")
            if status == "completed":
                completed.append(task)
            elif status in ["pending", "carried_forward"]:
                # Check if overdue (due_date is today but not completed)
                pending.append(task)
            else:
                pending.append(task)

        return {
            "pending": pending,
            "completed": completed,
            "overdue": [],  # Overdue would be past dates, not today
            "pending_count": len(pending),
            "completed_count": len(completed),
            "overdue_count": 0,
        }

    async def bulk_complete(self, task_ids: List[UUID]) -> int:
        """Bulk complete tasks."""
        update_data = {
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        count = 0
        for task_id in task_ids:
            response = (
                supabase.table("tasks")
                .update(update_data)
                .eq("id", str(task_id))
                .eq("user_id", str(self.user_id))
                .execute()
            )
            if response.data:
                count += 1
        return count

    async def bulk_carry_forward(
        self, task_ids: List[UUID], new_date: date
    ) -> int:
        """Bulk carry forward tasks."""
        count = 0
        for task_id in task_ids:
            try:
                await self.carry_forward(task_id, new_date)
                count += 1
            except Exception:
                continue
        return count
