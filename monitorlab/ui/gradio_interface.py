"""Gradio-based chat interface for MonitorLab."""

import asyncio
import logging
from typing import List, Tuple, Optional
import gradio as gr
from datetime import datetime

from monitorlab.agents import GenericTestAgent, HomepageAgent, AuthenticationAgent, CheckoutAgent
from monitorlab.graph.orchestrator import TestOrchestrator
from monitorlab.database import TestRunRepository, init_db
from monitorlab.config.settings import get_settings
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class MonitorLabChat:
    """Chat interface handler for MonitorLab."""

    def __init__(self):
        """Initialize chat interface."""
        self.settings = get_settings()
        self.llm = ChatOpenAI(
            base_url=self.settings.llm_api_base,
            api_key=self.settings.llm_api_key,
            model=self.settings.llm_model,
            temperature=0.7,
        )
        self.orchestrator = None
        asyncio.create_task(self._initialize())

    async def _initialize(self):
        """Initialize async resources."""
        await init_db(self.settings.database_url)
        logger.info("Chat interface initialized")

    async def process_message(
        self, message: str, history: List[Tuple[str, str]]
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """Process a user message and return response.

        Args:
            message: User message
            history: Chat history

        Returns:
            Tuple of (response, updated_history)
        """
        try:
            # Use LLM to determine what kind of test is needed
            planning_prompt = f"""User request: {message}

Analyze this request and determine:
1. What type of test is needed?
2. What is the target URL (if any)?
3. What specific agents should be spawned?

Respond in JSON format:
{{
    "test_type": "generic|homepage|auth|checkout|custom",
    "target_url": "URL or null",
    "agents": [
        {{"type": "agent_type", "task": "specific task description"}},
        ...
    ],
    "execution_mode": "parallel|sequential"
}}"""

            plan_response = await self.llm.ainvoke([("user", planning_prompt)])
            plan_text = plan_response.content

            # For now, create a generic agent for all requests
            # In production, would parse the LLM response and create appropriate agents

            # Extract URL if present (simple regex would work here)
            import re
            url_match = re.search(r'https?://[^\s]+', message)
            target_url = url_match.group(0) if url_match else None

            response = f"🤖 **Understanding your request...**\n\n"
            response += f"Planning test for: {message}\n\n"

            if target_url:
                response += f"Target URL: `{target_url}`\n\n"

                # Create orchestrator and agent
                orchestrator = TestOrchestrator(self.settings)
                await orchestrator.initialize()

                # Determine agent type based on keywords
                message_lower = message.lower()

                if "homepage" in message_lower or "home page" in message_lower:
                    agent = HomepageAgent(target_url=target_url, settings=self.settings)
                    response += "✅ Using **Homepage Agent**\n\n"
                elif "login" in message_lower or "auth" in message_lower or "sign in" in message_lower:
                    agent = AuthenticationAgent(target_url=target_url, settings=self.settings)
                    response += "✅ Using **Authentication Agent**\n\n"
                elif "checkout" in message_lower or "cart" in message_lower:
                    agent = CheckoutAgent(target_url=target_url, settings=self.settings)
                    response += "✅ Using **Checkout Agent**\n\n"
                else:
                    agent = GenericTestAgent(task=message, target_url=target_url, settings=self.settings)
                    response += "✅ Using **Generic Test Agent**\n\n"

                orchestrator.add_agent(agent)

                response += "🚀 **Running test...**\n\n"

                # Run the test
                result = await orchestrator.run_parallel(name=f"Chat: {message[:50]}")

                # Format results
                stats = result["statistics"]
                response += "📊 **Test Results:**\n\n"
                response += f"- Test Run ID: #{stats['test_run_id']}\n"
                response += f"- Status: {stats['status']}\n"
                response += f"- Success Rate: {stats['success_rate']}\n"
                response += f"- Duration: {stats['duration_seconds']:.2f}s\n\n"

                # Add agent results
                for agent_result in result["results"]:
                    if isinstance(agent_result, dict) and not agent_result.get("error"):
                        response += f"✅ **{agent_result['agent_name']}**: {agent_result['status']}\n"
                        if agent_result["screenshots"]:
                            response += f"   📸 Screenshots: {len(agent_result['screenshots'])}\n"
                    else:
                        error = agent_result.get("error", "Unknown error")
                        response += f"❌ **Agent failed**: {error}\n"

            else:
                response += "❓ No URL detected in your message. Please provide a URL to test.\n\n"
                response += "**Example:** Check if https://example.com loads correctly"

            return response

        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            return f"❌ **Error:** {str(e)}"

    async def get_recent_runs(self) -> str:
        """Get recent test runs.

        Returns:
            Formatted string of recent runs
        """
        try:
            runs = await TestRunRepository.get_recent_test_runs(limit=10)

            if not runs:
                return "No test runs yet."

            output = "## Recent Test Runs\n\n"
            for run in runs:
                output += f"**#{run.id}** - {run.name}\n"
                output += f"- Status: {run.status}\n"
                output += f"- Started: {run.started_at.strftime('%Y-%m-%d %H:%M')}\n"
                output += f"- Duration: {run.duration_seconds:.2f}s\n\n" if run.duration_seconds else "- Duration: N/A\n\n"

            return output

        except Exception as e:
            logger.exception(f"Error getting recent runs: {e}")
            return f"Error: {str(e)}"


def create_gradio_interface() -> gr.Blocks:
    """Create the Gradio interface.

    Returns:
        Gradio Blocks interface
    """
    chat_handler = MonitorLabChat()

    with gr.Blocks(title="MonitorLab", theme=gr.themes.Soft()) as interface:
        gr.Markdown("""
        # 🔬 MonitorLab
        ### AI-Enhanced Website Monitoring & Validation

        Ask me to test any website functionality! I'll spawn autonomous agents to validate your sites.

        **Examples:**
        - "Check if https://example.com loads correctly"
        - "Test the login form at https://myapp.com/login"
        - "Verify the checkout flow on https://shop.com/cart"
        """)

        with gr.Tab("💬 Chat"):
            chatbot = gr.Chatbot(
                label="MonitorLab Assistant",
                height=500,
                type="messages"
            )
            msg = gr.Textbox(
                label="Your Message",
                placeholder="E.g., Test https://example.com homepage",
                lines=2
            )
            submit = gr.Button("🚀 Run Test", variant="primary")
            clear = gr.Button("🗑️ Clear")

            async def respond(message, chat_history):
                if not message:
                    return "", chat_history

                # Add user message
                chat_history.append({"role": "user", "content": message})

                # Get response
                response = await chat_handler.process_message(message, chat_history)

                # Add assistant response
                chat_history.append({"role": "assistant", "content": response})

                return "", chat_history

            submit.click(respond, [msg, chatbot], [msg, chatbot])
            msg.submit(respond, [msg, chatbot], [msg, chatbot])
            clear.click(lambda: ([], ""), None, [chatbot, msg])

        with gr.Tab("📊 Test History"):
            gr.Markdown("## Recent Test Runs")
            history_display = gr.Markdown()
            refresh_btn = gr.Button("🔄 Refresh History")

            async def load_history():
                return await chat_handler.get_recent_runs()

            refresh_btn.click(load_history, None, history_display)
            interface.load(load_history, None, history_display)

        with gr.Tab("⚙️ Settings"):
            gr.Markdown("""
            ## Configuration

            MonitorLab uses:
            - **LLM:** Local model via LM Studio (OpenAI-compatible API)
            - **Vision:** Qwen2-VL-4B for visual validation
            - **Browser:** Playwright via MCP
            - **Orchestration:** LangGraph for multi-agent coordination
            - **Database:** SQLite for run history

            ### Setup
            1. Install and start LM Studio
            2. Load Qwen2-VL-4B-Instruct model
            3. Start the Local Server (port 1234)
            4. Configure `.env` file with your settings
            """)

            with gr.Accordion("Current Settings", open=False):
                settings = chat_handler.settings
                gr.Markdown(f"""
                - **LLM API:** `{settings.llm_api_base}`
                - **LLM Model:** `{settings.llm_model}`
                - **Vision Model:** `{settings.vision_model}`
                - **Database:** `{settings.database_url}`
                - **Max Concurrent Agents:** `{settings.max_concurrent_agents}`
                """)

    return interface


def launch_ui(share: bool = False, server_port: Optional[int] = None):
    """Launch the Gradio UI.

    Args:
        share: Whether to create a public share link
        server_port: Optional port (default from settings)
    """
    settings = get_settings()
    port = server_port or settings.gradio_server_port

    interface = create_gradio_interface()
    interface.launch(
        server_port=port,
        share=share or settings.gradio_share,
        server_name="0.0.0.0",
    )


if __name__ == "__main__":
    launch_ui()
