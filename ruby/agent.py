import json
import logging
import re
from config.settings import settings
from ruby.brain import Brain
from ruby.tools import create_registry
from ruby.memory.obsidian import ObsidianMemory
from ruby.memory.embeddings import VectorMemory

logger = logging.getLogger("ruby.agent")

TOOL_CALL_RE = re.compile(r"```tool\s*\n(.*?)\n```", re.DOTALL)

class ToolCall:
    def __init__(self, name: str, args: dict):
        self.name = name
        self.args = args

class AutonomousAgent:
    def __init__(self, brain: Brain):
        self.brain = brain
        self.tools = create_registry()
        self.obsidian = ObsidianMemory()
        self.vector_memory = VectorMemory(brain)
        self.max_steps = settings.MAX_PLAN_STEPS
        self.tool_results = []

    def process(self, user_input: str) -> str:
        context = self.obsidian.get_context(user_input)
        vec_context = self.vector_memory.get_context(user_input)
        if vec_context:
            context = f"{context}\n\n{vec_context}" if context else vec_context

        system_extra = (
            "You have tools available. When you want to use a tool, "
            "respond with a tool call in this format:\n"
            "```tool\n{\"name\": \"tool_name\", \"args\": {...}}\n```\n"
            "Then wait for the result and continue.\n"
            f"Available tools: {', '.join(self.tools.list_names())}\n\n"
            "If a tool returns [NEEDS_CONFIRMATION], ask the user before proceeding."
        )

        self.brain.system_prompt += f"\n\n{system_extra}"
        logger.info("Processing: %s", user_input[:100])

        if settings.AUTONOMOUS_MODE:
            return self._autonomous_process(user_input, context)
        else:
            return self.brain.think(user_input, context)

    def _autonomous_process(self, user_input: str, context: str) -> str:
        plan = self._create_plan(user_input, context)
        logger.info("Plan: %s", json.dumps(plan, indent=2))
        results = []

        for step in plan["steps"]:
            logger.info("Executing step: %s", step["description"])
            result = self._execute_step(step)
            results.append({
                "step": step["description"],
                "result": result
            })

        summary_prompt = (
            f"Original request: {user_input}\n\n"
            f"Steps and results:\n{json.dumps(results, indent=2)}\n\n"
            "Summarise what was accomplished for the user."
        )
        return self.brain.think(summary_prompt)

    def _create_plan(self, user_input: str, context: str) -> dict:
        plan_prompt = (
            f"User request: {user_input}\n"
            f"Context: {context[:1000]}\n\n"
            "Create a step-by-step plan to fulfill this request.\n"
            f"Available tools: {', '.join(self.tools.list_names())}\n\n"
            "Respond with JSON:\n"
            '{"steps": [{"description": "what to do", "tool": "tool_name", "args": {...}}]}'
        )
        return self.brain.structured_query(plan_prompt)

    def _execute_step(self, step: dict) -> str:
        tool_name = step.get("tool")
        args = step.get("args", {})

        if not tool_name or tool_name not in self.tools.list_names():
            return f"Cannot execute step: tool '{tool_name}' not available"

        result = self.tools.execute(tool_name, **args)

        if isinstance(result, str) and result.startswith("[NEEDS_CONFIRMATION]"):
            question = result.replace("[NEEDS_CONFIRMATION] ", "")
            logger.info("Need confirmation: %s", question)
            return f"[WAITING_FOR_USER] {question}"

        return str(result)

    def execute_tool_call(self, tool_call_str: str) -> str:
        try:
            match = TOOL_CALL_RE.search(tool_call_str)
            if not match:
                return "No tool call found in response"

            data = json.loads(match.group(1))
            name = data["name"]
            args = data.get("args", {})

            logger.info("Tool call: %s with args: %s", name, args)
            result = self.tools.execute(name, **args)

            if isinstance(result, str) and result.startswith("[NEEDS_CONFIRMATION]"):
                return result

            self.tool_results.append({"tool": name, "result": result})
            return result

        except json.JSONDecodeError as e:
            return f"Invalid JSON in tool call: {e}"
        except Exception as e:
            return f"Tool execution error: {e}"

    def process_with_tools(self, user_input: str) -> str:
        context = self.obsidian.get_context(user_input)
        vec_context = self.vector_memory.get_context(user_input)
        if vec_context:
            context = f"{context}\n\n{vec_context}" if context else vec_context

        max_loops = 5
        full_response = ""
        current_input = user_input

        for i in range(max_loops):
            response = self.brain.think(current_input, context)

            if TOOL_CALL_RE.search(response):
                tool_result = self.execute_tool_call(response)
                full_response += f"{response}\n\n[Tool Result: {tool_result[:500]}]\n\n"
                current_input = (
                    f"I used a tool. Result: {tool_result[:500]}\n"
                    "Continue based on this result."
                )
                context = self.obsidian.get_context(current_input)
            else:
                full_response += response
                break

        return full_response
