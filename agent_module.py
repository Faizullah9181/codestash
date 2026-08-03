"""Renders ``app/agentic/agent/agent.py`` for a generated project.

The selected provider, orchestration framework and agentic pattern are fused into
one module that drives the framework's real SDK — ``google.adk``, ``langgraph``,
``langchain``, ``crewai``, ``agents`` (OpenAI Agents) or ``strands``.

Every framework renderer supplies the same seven slots, so the surrounding module
skeleton and the public ``Agent`` contract stay identical across all combinations.
"""

from __future__ import annotations

PROVIDER_LABELS = {
    "openai": "OpenAI",
    "gemini": "Gemini",
    "anthropic": "Anthropic",
    "groq": "Groq",
    "openrouter": "OpenRouter",
    "azure-openai": "Azure OpenAI",
    "ollama": "Ollama",
    "openai-compatible": "OpenAI-compatible",
}

FRAMEWORK_LABELS = {
    "google-adk": "Google ADK",
    "langgraph": "LangGraph",
    "langchain": "LangChain",
    "crewai": "CrewAI",
    "openai-agents": "OpenAI Agents",
    "strands": "Strands Agents",
}

# LiteLLM routes every non-native provider for ADK and CrewAI.
LITELLM_PREFIXES = {
    "openai": "openai",
    "gemini": "gemini",
    "anthropic": "anthropic",
    "groq": "groq",
    "openrouter": "openrouter",
    "azure-openai": "azure",
    "ollama": "ollama_chat",
    "openai-compatible": "openai",
}

# Providers that speak the OpenAI wire protocol and therefore need a base URL.
OPENAI_WIRE = {"openai", "groq", "openrouter", "ollama", "openai-compatible", "azure-openai"}


# --------------------------------------------------------------------------
# Patterns
# --------------------------------------------------------------------------
# Each pattern maps onto one of five topologies. The topology decides which
# framework primitive is used; the roles and instruction keep every pattern
# distinct even when two share a topology.

PATTERN_SPECS: dict[str, dict] = {
    "react": {
        "topology": "single",
        "instruction": (
            "You are a ReAct agent. Reason step by step about the request, call a tool "
            "when it would give you information you do not already have, then answer.\n"
            "State your reasoning briefly before the final answer."
        ),
        "roles": (),
    },
    "tool-use": {
        "topology": "single",
        "instruction": (
            "You are a tool-using assistant. Prefer calling a tool over guessing.\n"
            "Chain several tool calls when one alone cannot answer the request, and "
            "ground every claim in the values the tools returned."
        ),
        "roles": (),
    },
    "autonomous": {
        "topology": "single",
        "instruction": (
            "You are an autonomous agent. Given a goal, decide your own next action, "
            "use tools to make progress, and keep working until the goal is met.\n"
            "Stop and report when the goal is satisfied or genuinely blocked."
        ),
        "roles": (),
    },
    "rag": {
        "topology": "single",
        "instruction": (
            "You are a retrieval-augmented agent. Search your knowledge sources first, "
            "then answer strictly from what you retrieved.\n"
            "If the retrieved context does not answer the question, say so instead of guessing."
        ),
        "roles": (),
    },
    "sequential": {
        "topology": "pipeline",
        "instruction": "You are one stage of a sequential pipeline.",
        "roles": (
            ("researcher", "Gather the facts the task depends on."),
            ("analyst", "Interpret those facts and draw conclusions."),
            ("writer", "Turn the analysis into the final answer."),
        ),
    },
    "planner-executor": {
        "topology": "pipeline",
        "instruction": "You are one stage of a plan-then-execute pipeline.",
        "roles": (
            ("planner", "Break the task into a short numbered plan."),
            ("executor", "Carry out the plan step by step and report the result."),
        ),
    },
    "planning": {
        "topology": "pipeline",
        "instruction": "You are one stage of a strategic planning pipeline.",
        "roles": (
            ("strategist", "Clarify the goal, constraints and success criteria."),
            ("planner", "Produce an ordered, actionable plan."),
            ("executor", "Execute the plan and summarise the outcome."),
        ),
    },
    "reflection": {
        "topology": "loop",
        "instruction": "You improve an answer through self-critique.",
        "roles": (
            ("drafter", "Write the best first answer you can."),
            ("critic", "Find concrete weaknesses in the draft. Be specific."),
            ("reviser", "Rewrite the draft, fixing every point the critic raised."),
        ),
        "rounds": 2,
    },
    "reviewer-critic": {
        "topology": "loop",
        "instruction": "You produce work that must survive editorial review.",
        "roles": (
            ("author", "Produce the work product."),
            ("reviewer", "Review it for accuracy, completeness and clarity."),
            ("editor", "Apply the review and publish the final version."),
        ),
        "rounds": 2,
    },
    "parallel": {
        "topology": "fanout",
        "instruction": "You handle one independent branch of a larger task.",
        "roles": (
            ("factual", "Cover the factual and technical angle."),
            ("risk", "Cover risks, edge cases and failure modes."),
            ("practical", "Cover practical steps and trade-offs."),
        ),
    },
    "swarm": {
        "topology": "fanout",
        "instruction": "You are one peer in a swarm working the same task independently.",
        "roles": (
            ("explorer", "Explore unconventional approaches."),
            ("optimizer", "Find the most efficient approach."),
            ("validator", "Stress-test the approaches for correctness."),
        ),
    },
    "debate": {
        "topology": "fanout",
        "instruction": "You argue one side of a debate. Make the strongest honest case.",
        "roles": (
            ("proponent", "Argue in favour, with evidence."),
            ("opponent", "Argue against, with evidence."),
        ),
    },
    "hierarchical": {
        "topology": "supervisor",
        "instruction": (
            "You are the supervisor. Break the task down, delegate each part to the "
            "specialist best suited to it, then combine their work into one answer."
        ),
        "roles": (
            ("researcher", "Finds and verifies information."),
            ("analyst", "Analyses data and draws conclusions."),
            ("writer", "Writes clear final prose."),
        ),
    },
    "coordinator": {
        "topology": "supervisor",
        "instruction": (
            "You are the coordinator. Route each request to the specialist that owns "
            "that domain, then reconcile their responses into one answer."
        ),
        "roles": (
            ("intake", "Clarifies and classifies the request."),
            ("specialist", "Handles the domain work."),
            ("reporter", "Reports the outcome to the user."),
        ),
    },
    "blackboard": {
        "topology": "supervisor",
        "instruction": (
            "You own the shared blackboard. Post the problem, let each specialist "
            "contribute what it knows, and synthesise the contributions into an answer."
        ),
        "roles": (
            ("observer", "Records the known facts on the blackboard."),
            ("reasoner", "Derives new conclusions from the blackboard."),
            ("resolver", "Resolves conflicts and produces the answer."),
        ),
    },
}


def _roles_constant(spec: dict) -> str:
    if not spec["roles"]:
        return ""
    lines = ",\n".join(f'    ("{n}", "{d}")' for n, d in spec["roles"])
    return f"ROLES: tuple[tuple[str, str], ...] = (\n{lines},\n)\n"


def _instructions_literal(text: str, width: int = 86) -> str:
    """Render the system prompt as wrapped, implicitly concatenated string literals.

    The runtime value is byte-identical to ``text``; only the source layout changes,
    which keeps every generated line inside the project's 100 character limit.
    """
    chunks: list[str] = []
    lines = text.split("\n")
    for index, line in enumerate(lines):
        pieces: list[str] = []
        current = ""
        for word in line.split(" "):
            candidate = f"{current} {word}" if current else word
            if len(candidate) > width and current:
                pieces.append(current + " ")
                current = word
            else:
                current = candidate
        pieces.append(current)
        if index < len(lines) - 1:
            pieces[-1] += "\\n"
        chunks.extend(pieces)
    if len(chunks) == 1 and len(chunks[0]) + len('INSTRUCTIONS = ""') <= 100:
        return f'INSTRUCTIONS = "{chunks[0]}"'
    body = "\n".join(f'    "{chunk}"' for chunk in chunks)
    return f"INSTRUCTIONS = (\n{body}\n)"


# --------------------------------------------------------------------------
# Google ADK
# --------------------------------------------------------------------------


def _adk(provider: str, pattern: str, spec: dict) -> dict:
    topology = spec["topology"]
    native_gemini = provider == "gemini"

    imports = [
        "from google.adk.agents import LlmAgent",
        "from google.adk.runners import Runner",
        "from google.adk.sessions import InMemorySessionService",
        "from google.genai import types as genai_types",
    ]
    if topology == "pipeline":
        imports.insert(1, "from google.adk.agents import SequentialAgent")
    elif topology == "loop":
        imports.insert(1, "from google.adk.agents import LoopAgent")
    elif topology == "fanout":
        imports.insert(1, "from google.adk.agents import ParallelAgent, SequentialAgent")
    if not native_gemini:
        imports.append("from google.adk.models.lite_llm import LiteLlm")

    if native_gemini:
        model_body = (
            '    """Gemini is ADK\'s native model family, so the id is passed directly."""\n'
            '    os.environ.setdefault("GOOGLE_API_KEY", config.provider.api_key)\n'
            '    os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")\n'
            "    return config.provider.model"
        )
    else:
        prefix = LITELLM_PREFIXES[provider]
        extra = (
            "\n        api_base=config.provider.base_url or None,"
            if provider in OPENAI_WIRE
            else ""
        )
        model_body = (
            f'    """ADK reaches {PROVIDER_LABELS[provider]} through LiteLLM."""\n'
            "    return LiteLlm(\n"
            f'        model=f"{prefix}/{{config.provider.model}}",\n'
            "        api_key=config.provider.api_key,"
            f"{extra}\n"
            "    )"
        )

    tools = (
        "def recall(query: str) -> dict:\n"
        '    """Look up previously stored context for the current task.\n\n'
        "    Args:\n"
        "        query: What to search the agent's memory for.\n"
        '    """\n'
        '    return {"query": query, "matches": []}\n\n\n'
        "TOOLS = [recall]\n"
    )

    if topology == "single":
        runtime_body = (
            f'    """One {FRAMEWORK_LABELS["google-adk"]} LlmAgent driving the {pattern} loop."""\n'
            "    return LlmAgent(\n"
            '        name=APP_NAME.replace("-", "_"),\n'
            "        model=build_model(config),\n"
            "        instruction=INSTRUCTIONS,\n"
            "        tools=TOOLS,\n"
            "        generate_content_config=genai_types.GenerateContentConfig(\n"
            "            temperature=config.provider.temperature,\n"
            "            max_output_tokens=config.provider.max_tokens,\n"
            "        ),\n"
            "    )"
        )
    elif topology == "pipeline":
        runtime_body = (
            '    """Each role becomes an ADK sub-agent; SequentialAgent runs them in order."""\n'
            "    model = build_model(config)\n"
            "    stages = [\n"
            "        LlmAgent(\n"
            "            name=role,\n"
            "            model=model,\n"
            '            instruction=f"{INSTRUCTIONS}\\n\\nYour role is {role}: {duty}",\n'
            "            output_key=role,\n"
            "            tools=TOOLS,\n"
            "        )\n"
            "        for role, duty in ROLES\n"
            "    ]\n"
            '    return SequentialAgent(name=APP_NAME.replace("-", "_"), sub_agents=stages)'
        )
    elif topology == "loop":
        runtime_body = (
            '    """LoopAgent re-runs the draft/critique/revise agents for ROUNDS iterations."""\n'
            "    model = build_model(config)\n"
            "    stages = [\n"
            "        LlmAgent(\n"
            "            name=role,\n"
            "            model=model,\n"
            '            instruction=f"{INSTRUCTIONS}\\n\\nYour role is {role}: {duty}",\n'
            "            output_key=role,\n"
            "            tools=TOOLS,\n"
            "        )\n"
            "        for role, duty in ROLES\n"
            "    ]\n"
            "    return LoopAgent(\n"
            '        name=APP_NAME.replace("-", "_"),\n'
            "        max_iterations=ROUNDS,\n"
            "        sub_agents=stages,\n"
            "    )"
        )
    elif topology == "fanout":
        runtime_body = (
            '    """ParallelAgent fans the task out; a final LlmAgent merges the branches."""\n'
            "    model = build_model(config)\n"
            "    branches = [\n"
            "        LlmAgent(\n"
            "            name=role,\n"
            "            model=model,\n"
            '            instruction=f"{INSTRUCTIONS}\\n\\nYour angle is {role}: {duty}",\n'
            "            output_key=role,\n"
            "            tools=TOOLS,\n"
            "        )\n"
            "        for role, duty in ROLES\n"
            "    ]\n"
            "    merger = LlmAgent(\n"
            '        name="merge",\n'
            "        model=model,\n"
            "        instruction=(\n"
            '            "Combine the branch results above into one coherent answer. "\n'
            '            "Resolve disagreements explicitly rather than averaging them."\n'
            "        ),\n"
            "    )\n"
            "    return SequentialAgent(\n"
            '        name=APP_NAME.replace("-", "_"),\n'
            '        sub_agents=[ParallelAgent(name="branches", sub_agents=branches), merger],\n'
            "    )"
        )
    else:  # supervisor
        runtime_body = (
            '    """A root LlmAgent that delegates to specialist sub-agents via ADK transfer."""\n'
            "    model = build_model(config)\n"
            "    specialists = [\n"
            "        LlmAgent(\n"
            "            name=role,\n"
            "            model=model,\n"
            "            description=duty,\n"
            '            instruction=f"You are the {role}. {duty}",\n'
            "            tools=TOOLS,\n"
            "        )\n"
            "        for role, duty in ROLES\n"
            "    ]\n"
            "    return LlmAgent(\n"
            '        name=APP_NAME.replace("-", "_"),\n'
            "        model=model,\n"
            "        instruction=INSTRUCTIONS,\n"
            "        sub_agents=specialists,\n"
            "    )"
        )

    invoke = (
        "        session = await self._sessions.create_session(app_name=APP_NAME, user_id=user_id)\n"
        "        runner = Runner(agent=self.runtime, app_name=APP_NAME, session_service=self._sessions)\n"
        '        message = genai_types.Content(role="user", parts=[genai_types.Part(text=task)])\n'
        '        final, transcript = "", ""\n'
        "        async for event in runner.run_async(\n"
        "            user_id=user_id, session_id=session.id, new_message=message\n"
        "        ):\n"
        '            for part in getattr(event.content, "parts", None) or []:\n'
        "                if not part.text:\n"
        "                    continue\n"
        "                transcript += part.text\n"
        "                if event.is_final_response():\n"
        "                    final += part.text\n"
        "        return (final or transcript).strip()"
    )

    stream = (
        "        session = await self._sessions.create_session(app_name=APP_NAME, user_id=user_id)\n"
        "        runner = Runner(agent=self.runtime, app_name=APP_NAME, session_service=self._sessions)\n"
        '        message = genai_types.Content(role="user", parts=[genai_types.Part(text=task)])\n'
        "        async for event in runner.run_async(\n"
        "            user_id=user_id, session_id=session.id, new_message=message\n"
        "        ):\n"
        '            for part in getattr(event.content, "parts", None) or []:\n'
        "                if part.text:\n"
        "                    yield part.text"
    )

    return {
        "imports": "\n".join(imports),
        # Only the native Gemini binding configures the SDK through the environment.
        "stdlib": ["import os"] if native_gemini else [],
        "tools": tools,
        "model_body": model_body,
        "runtime_body": runtime_body,
        "init_extra": "        self._sessions = InMemorySessionService()",
        "invoke": invoke,
        "stream": stream,
    }


# --------------------------------------------------------------------------
# LangChain model binding (shared with LangGraph)
# --------------------------------------------------------------------------


def _langchain_model(provider: str) -> tuple[list[str], str]:
    if provider == "gemini":
        return (
            ["from langchain_google_genai import ChatGoogleGenerativeAI"],
            '    """Native LangChain binding for Gemini."""\n'
            "    return ChatGoogleGenerativeAI(\n"
            "        model=config.provider.model,\n"
            "        google_api_key=config.provider.api_key,\n"
            "        temperature=config.provider.temperature,\n"
            "        max_output_tokens=config.provider.max_tokens,\n"
            "    )",
        )
    if provider == "anthropic":
        return (
            ["from langchain_anthropic import ChatAnthropic"],
            '    """Native LangChain binding for Anthropic."""\n'
            "    return ChatAnthropic(\n"
            "        model=config.provider.model,\n"
            "        api_key=config.provider.api_key,\n"
            "        temperature=config.provider.temperature,\n"
            "        max_tokens=config.provider.max_tokens,\n"
            "    )",
        )
    if provider == "azure-openai":
        return (
            ["from langchain_openai import AzureChatOpenAI"],
            '    """Azure deployments are addressed by deployment name, not model id."""\n'
            "    return AzureChatOpenAI(\n"
            "        azure_deployment=config.provider.model,\n"
            "        azure_endpoint=config.provider.base_url,\n"
            "        api_key=config.provider.api_key,\n"
            '        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),\n'
            "        temperature=config.provider.temperature,\n"
            "        max_tokens=config.provider.max_tokens,\n"
            "    )",
        )
    label = PROVIDER_LABELS[provider]
    note = f'    """{label} is reached through the OpenAI-compatible chat completions API."""\n'
    return (
        ["from langchain_openai import ChatOpenAI"],
        note + "    return ChatOpenAI(\n"
        "        model=config.provider.model,\n"
        '        api_key=config.provider.api_key or "not-needed",\n'
        "        base_url=config.provider.base_url or None,\n"
        "        temperature=config.provider.temperature,\n"
        "        max_tokens=config.provider.max_tokens,\n"
        "    )",
    )


# --------------------------------------------------------------------------
# LangGraph
# --------------------------------------------------------------------------


def _langgraph(provider: str, pattern: str, spec: dict) -> dict:
    topology = spec["topology"]
    model_imports, model_body = _langchain_model(provider)

    imports = list(model_imports) + ["from langchain_core.tools import tool"]
    if topology == "single":
        imports.append("from langgraph.prebuilt import create_react_agent")
    else:
        imports.append("from langgraph.graph import END, START, StateGraph")
        imports.append("from langgraph.graph.message import MessagesState")

    tools = (
        "@tool\n"
        "def recall(query: str) -> str:\n"
        '    """Look up previously stored context for the current task."""\n'
        '    return f"no stored context for {query!r} yet"\n\n\n'
        "TOOLS = [recall]\n"
    )

    if topology == "single":
        runtime_body = (
            '    """LangGraph\'s prebuilt ReAct graph: model + tool loop + state."""\n'
            "    return create_react_agent(\n"
            "        build_model(config),\n"
            "        tools=TOOLS,\n"
            "        prompt=INSTRUCTIONS,\n"
            "    )"
        )
    elif topology in {"pipeline", "loop"}:
        repeat = "ROUNDS" if topology == "loop" else "1"
        runtime_body = (
            '    """One StateGraph node per role, wired START -> ... -> END."""\n'
            "    model = build_model(config)\n"
            "    graph = StateGraph(MessagesState)\n\n"
            "    def make_node(role: str, duty: str):\n"
            "        async def node(state: MessagesState) -> dict:\n"
            '            prompt = f"{INSTRUCTIONS}\\n\\nYour role is {role}: {duty}"\n'
            '            reply = await model.ainvoke([("system", prompt), *state["messages"]])\n'
            '            return {"messages": [reply]}\n\n'
            "        return node\n\n"
            f'    sequence = [f"{{role}}_{{turn}}" for turn in range({repeat}) for role, _ in ROLES]\n'
            "    duties = {role: duty for role, duty in ROLES}\n"
            "    for node_id in sequence:\n"
            '        role = node_id.rsplit("_", 1)[0]\n'
            "        graph.add_node(node_id, make_node(role, duties[role]))\n"
            "    graph.add_edge(START, sequence[0])\n"
            "    for source, target in zip(sequence, sequence[1:]):\n"
            "        graph.add_edge(source, target)\n"
            "    graph.add_edge(sequence[-1], END)\n"
            "    return graph.compile()"
        )
    elif topology == "fanout":
        runtime_body = (
            '    """Fan out to one node per role in parallel, then merge in a join node."""\n'
            "    model = build_model(config)\n"
            "    graph = StateGraph(MessagesState)\n\n"
            "    def make_branch(role: str, duty: str):\n"
            "        async def node(state: MessagesState) -> dict:\n"
            '            prompt = f"{INSTRUCTIONS}\\n\\nYour angle is {role}: {duty}"\n'
            '            reply = await model.ainvoke([("system", prompt), *state["messages"]])\n'
            '            return {"messages": [reply]}\n\n'
            "        return node\n\n"
            "    async def merge(state: MessagesState) -> dict:\n"
            "        reply = await model.ainvoke(\n"
            "            [\n"
            "                (\n"
            '                    "system",\n'
            '                    "Combine the preceding branch answers into one coherent "\n'
            '                    "response. Resolve disagreements explicitly.",\n'
            "                ),\n"
            '                *state["messages"],\n'
            "            ]\n"
            "        )\n"
            '        return {"messages": [reply]}\n\n'
            "    for role, duty in ROLES:\n"
            "        graph.add_node(role, make_branch(role, duty))\n"
            "        graph.add_edge(START, role)\n"
            '        graph.add_edge(role, "merge")\n'
            '    graph.add_node("merge", merge)\n'
            '    graph.add_edge("merge", END)\n'
            "    return graph.compile()"
        )
    else:  # supervisor
        runtime_body = (
            '    """A supervisor node routes to a specialist node, then back to finish."""\n'
            "    model = build_model(config)\n"
            "    graph = StateGraph(MessagesState)\n"
            "    duties = {role: duty for role, duty in ROLES}\n\n"
            "    async def supervisor(state: MessagesState) -> dict:\n"
            '        roster = "\\n".join(f"- {r}: {d}" for r, d in ROLES)\n'
            "        reply = await model.ainvoke(\n"
            "            [\n"
            '                ("system", f"{INSTRUCTIONS}\\n\\nSpecialists:\\n{roster}"),\n'
            '                *state["messages"],\n'
            "            ]\n"
            "        )\n"
            '        return {"messages": [reply]}\n\n'
            "    def make_specialist(role: str, duty: str):\n"
            "        async def node(state: MessagesState) -> dict:\n"
            "            reply = await model.ainvoke(\n"
            '                [("system", f"You are the {role}. {duty}"), *state["messages"]]\n'
            "            )\n"
            '            return {"messages": [reply]}\n\n'
            "        return node\n\n"
            '    graph.add_node("supervisor", supervisor)\n'
            '    graph.add_edge(START, "supervisor")\n'
            "    for role, duty in ROLES:\n"
            "        graph.add_node(role, make_specialist(role, duties[role]))\n"
            '        graph.add_edge("supervisor", role)\n'
            "        graph.add_edge(role, END)\n"
            "    return graph.compile()"
        )

    invoke = (
        "        del user_id\n"
        '        state = await self.runtime.ainvoke({"messages": [("user", task)]})\n'
        '        messages = state["messages"]\n'
        '        return str(getattr(messages[-1], "content", "")).strip()'
    )
    stream = (
        "        del user_id\n"
        "        async for chunk, _meta in self.runtime.astream(\n"
        '            {"messages": [("user", task)]}, stream_mode="messages"\n'
        "        ):\n"
        '            text = getattr(chunk, "content", "")\n'
        "            if text:\n"
        "                yield str(text)"
    )

    stdlib = ["import os"] if provider == "azure-openai" else []
    return {
        "imports": "\n".join(imports),
        "stdlib": stdlib,
        "tools": tools,
        "model_body": model_body,
        "runtime_body": runtime_body,
        "init_extra": "",
        "invoke": invoke,
        "stream": stream,
    }


# --------------------------------------------------------------------------
# LangChain
# --------------------------------------------------------------------------


def _langchain(provider: str, pattern: str, spec: dict) -> dict:
    topology = spec["topology"]
    model_imports, model_body = _langchain_model(provider)

    imports = list(model_imports) + [
        "from langchain_core.tools import tool",
    ]
    if topology == "single":
        # LangChain 1.x builds tool-calling agents with create_agent.
        imports.append("from langchain.agents import create_agent")
    else:
        imports.append("from langchain_core.prompts import ChatPromptTemplate")
        imports.append("from langchain_core.output_parsers import StrOutputParser")
        if topology == "fanout":
            imports.append("from langchain_core.runnables import RunnableParallel")

    tools = (
        "@tool\n"
        "def recall(query: str) -> str:\n"
        '    """Look up previously stored context for the current task."""\n'
        '    return f"no stored context for {query!r} yet"\n\n\n'
        "TOOLS = [recall]\n"
    )

    if topology == "single":
        runtime_body = (
            '    """LangChain\'s create_agent builds the model + tool-calling loop."""\n'
            "    return create_agent(\n"
            "        build_model(config),\n"
            "        tools=TOOLS,\n"
            "        system_prompt=INSTRUCTIONS,\n"
            "        name=APP_NAME,\n"
            "    )"
        )
    elif topology in {"pipeline", "loop"}:
        repeat = "ROUNDS" if topology == "loop" else "1"
        runtime_body = (
            '    """Compose one LCEL chain per role and run them in order."""\n'
            "    model = build_model(config)\n"
            "    stages = []\n"
            f"    for _ in range({repeat}):\n"
            "        for role, duty in ROLES:\n"
            "            prompt = ChatPromptTemplate.from_messages(\n"
            "                [\n"
            "                    (\n"
            '                        "system",\n'
            '                        f"{INSTRUCTIONS}\\n\\nYour role is {role}: {duty}",\n'
            "                    ),\n"
            '                    ("human", "{input}"),\n'
            "                ]\n"
            "            )\n"
            "            stages.append((role, prompt | model | StrOutputParser()))\n"
            "    return stages"
        )
    elif topology == "fanout":
        runtime_body = (
            '    """RunnableParallel evaluates every branch concurrently, then a merge chain."""\n'
            "    model = build_model(config)\n"
            "    branches = {}\n"
            "    for role, duty in ROLES:\n"
            "        prompt = ChatPromptTemplate.from_messages(\n"
            "            [\n"
            '                ("system", f"{INSTRUCTIONS}\\n\\nYour angle is {role}: {duty}"),\n'
            '                ("human", "{input}"),\n'
            "            ]\n"
            "        )\n"
            "        branches[role] = prompt | model | StrOutputParser()\n"
            "    merge = (\n"
            "        ChatPromptTemplate.from_messages(\n"
            "            [\n"
            "                (\n"
            '                    "system",\n'
            '                    "Combine the branch answers into one coherent response. "\n'
            '                    "Resolve disagreements explicitly.",\n'
            "                ),\n"
            '                ("human", "Task: {input}\\n\\nBranches:\\n{branches}"),\n'
            "            ]\n"
            "        )\n"
            "        | model\n"
            "        | StrOutputParser()\n"
            "    )\n"
            "    return RunnableParallel(**branches), merge"
        )
    else:  # supervisor
        runtime_body = (
            '    """A supervisor chain delegates to one specialist chain per role."""\n'
            "    model = build_model(config)\n"
            '    roster = "\\n".join(f"- {r}: {d}" for r, d in ROLES)\n'
            "    supervisor = (\n"
            "        ChatPromptTemplate.from_messages(\n"
            "            [\n"
            '                ("system", f"{INSTRUCTIONS}\\n\\nSpecialists:\\n{roster}"),\n'
            '                ("human", "{input}"),\n'
            "            ]\n"
            "        )\n"
            "        | model\n"
            "        | StrOutputParser()\n"
            "    )\n"
            "    specialists = {}\n"
            "    for role, duty in ROLES:\n"
            "        prompt = ChatPromptTemplate.from_messages(\n"
            "            [\n"
            '                ("system", f"You are the {role}. {duty}"),\n'
            '                ("human", "Task: {input}\\n\\nSupervisor brief:\\n{brief}"),\n'
            "            ]\n"
            "        )\n"
            "        specialists[role] = prompt | model | StrOutputParser()\n"
            "    return supervisor, specialists"
        )

    if topology == "single":
        invoke = (
            "        del user_id\n"
            '        state = await self.runtime.ainvoke({"messages": [("user", task)]})\n'
            '        return str(getattr(state["messages"][-1], "content", "")).strip()'
        )
        stream = (
            "        del user_id\n"
            "        async for chunk, _meta in self.runtime.astream(\n"
            '            {"messages": [("user", task)]}, stream_mode="messages"\n'
            "        ):\n"
            '            text = getattr(chunk, "content", "")\n'
            "            if text:\n"
            "                yield str(text)"
        )
    elif topology in {"pipeline", "loop"}:
        invoke = (
            "        del user_id\n"
            "        carried = task\n"
            "        for role, chain in self.runtime:\n"
            '            carried = await chain.ainvoke({"input": carried})\n'
            '            self._steps.append({"role": role, "output": carried})\n'
            "        return str(carried).strip()"
        )
        stream = "        yield await self._invoke(task, user_id)"
    elif topology == "fanout":
        invoke = (
            "        del user_id\n"
            "        fanout, merge = self.runtime\n"
            '        branches = await fanout.ainvoke({"input": task})\n'
            '        self._steps.extend({"role": role, "output": text} for role, text in branches.items())\n'
            '        rendered = "\\n\\n".join(f"[{r}]\\n{t}" for r, t in branches.items())\n'
            '        merged = await merge.ainvoke({"input": task, "branches": rendered})\n'
            "        return str(merged).strip()"
        )
        stream = "        yield await self._invoke(task, user_id)"
    else:
        invoke = (
            "        del user_id\n"
            "        supervisor, specialists = self.runtime\n"
            '        brief = await supervisor.ainvoke({"input": task})\n'
            '        self._steps.append({"role": "supervisor", "output": brief})\n'
            "        results = []\n"
            "        for role, chain in specialists.items():\n"
            '            text = await chain.ainvoke({"input": task, "brief": brief})\n'
            '            self._steps.append({"role": role, "output": text})\n'
            '            results.append(f"[{role}]\\n{text}")\n'
            '        return "\\n\\n".join([brief, *results]).strip()'
        )
        stream = "        yield await self._invoke(task, user_id)"

    stdlib = ["import os"] if provider == "azure-openai" else []
    return {
        "imports": "\n".join(imports),
        "stdlib": stdlib,
        "tools": tools,
        "model_body": model_body,
        "runtime_body": runtime_body,
        "init_extra": "",
        "invoke": invoke,
        "stream": stream,
    }


# --------------------------------------------------------------------------
# CrewAI
# --------------------------------------------------------------------------


def _crewai(provider: str, pattern: str, spec: dict) -> dict:
    topology = spec["topology"]
    prefix = LITELLM_PREFIXES[provider]
    base_url = (
        "\n        base_url=config.provider.base_url or None," if provider in OPENAI_WIRE else ""
    )

    imports = [
        "from crewai import LLM, Agent as CrewAgent, Crew, Process, Task",
        "from crewai.tools import tool",
    ]

    model_body = (
        f'    """CrewAI resolves {PROVIDER_LABELS[provider]} through its LiteLLM-backed LLM."""\n'
        "    return LLM(\n"
        f'        model=f"{prefix}/{{config.provider.model}}",\n'
        "        api_key=config.provider.api_key or None,"
        f"{base_url}\n"
        "        temperature=config.provider.temperature,\n"
        "        max_tokens=config.provider.max_tokens,\n"
        "    )"
    )

    tools = (
        '@tool("recall")\n'
        "def recall(query: str) -> str:\n"
        '    """Look up previously stored context for the current task."""\n'
        '    return f"no stored context for {query!r} yet"\n\n\n'
        "TOOLS = [recall]\n"
    )

    if topology == "single":
        runtime_body = (
            '    """A single-member crew: one agent, one task."""\n'
            "    llm = build_model(config)\n"
            "    worker = CrewAgent(\n"
            "        role=APP_NAME,\n"
            '        goal="Answer the user\'s task completely and accurately.",\n'
            "        backstory=INSTRUCTIONS,\n"
            "        llm=llm,\n"
            "        tools=TOOLS,\n"
            "        verbose=False,\n"
            "    )\n"
            "    job = Task(\n"
            '        description="{task}",\n'
            '        expected_output="A complete, well-supported answer.",\n'
            "        agent=worker,\n"
            "    )\n"
            "    return Crew(agents=[worker], tasks=[job], process=Process.sequential)"
        )
    elif topology in {"pipeline", "loop"}:
        repeat = "ROUNDS" if topology == "loop" else "1"
        runtime_body = (
            '    """One crew member per role; CrewAI runs the tasks sequentially."""\n'
            "    llm = build_model(config)\n"
            "    members, jobs = [], []\n"
            f"    for turn in range({repeat}):\n"
            "        for role, duty in ROLES:\n"
            "            member = CrewAgent(\n"
            '                role=f"{role}-{turn}" if turn else role,\n'
            "                goal=duty,\n"
            '                backstory=f"{INSTRUCTIONS}\\n\\nYou are the {role}.",\n'
            "                llm=llm,\n"
            "                tools=TOOLS,\n"
            "                verbose=False,\n"
            "            )\n"
            "            members.append(member)\n"
            "            jobs.append(\n"
            "                Task(\n"
            '                    description=f"{duty}\\n\\nTask: {{task}}",\n'
            "                    expected_output=duty,\n"
            "                    agent=member,\n"
            "                    context=jobs[-1:],\n"
            "                )\n"
            "            )\n"
            "    return Crew(agents=members, tasks=jobs, process=Process.sequential)"
        )
    elif topology == "fanout":
        runtime_body = (
            '    """Branch tasks run with async_execution; a merge task joins them."""\n'
            "    llm = build_model(config)\n"
            "    members, jobs = [], []\n"
            "    for role, duty in ROLES:\n"
            "        member = CrewAgent(\n"
            "            role=role,\n"
            "            goal=duty,\n"
            '            backstory=f"{INSTRUCTIONS}\\n\\nYour angle is {role}.",\n'
            "            llm=llm,\n"
            "            tools=TOOLS,\n"
            "            verbose=False,\n"
            "        )\n"
            "        members.append(member)\n"
            "        jobs.append(\n"
            "            Task(\n"
            '                description=f"{duty}\\n\\nTask: {{task}}",\n'
            "                expected_output=duty,\n"
            "                agent=member,\n"
            "                async_execution=True,\n"
            "            )\n"
            "        )\n"
            "    merger = CrewAgent(\n"
            '        role="merge",\n'
            '        goal="Combine the branch results into one coherent answer.",\n'
            '        backstory="You reconcile parallel findings and resolve disagreements.",\n'
            "        llm=llm,\n"
            "        verbose=False,\n"
            "    )\n"
            "    members.append(merger)\n"
            "    jobs.append(\n"
            "        Task(\n"
            '            description="Combine every branch result into one answer.",\n'
            '            expected_output="One reconciled answer.",\n'
            "            agent=merger,\n"
            "            context=list(jobs),\n"
            "        )\n"
            "    )\n"
            "    return Crew(agents=members, tasks=jobs, process=Process.sequential)"
        )
    else:  # supervisor
        runtime_body = (
            '    """Process.hierarchical gives CrewAI an auto-generated manager agent."""\n'
            "    llm = build_model(config)\n"
            "    members = [\n"
            "        CrewAgent(\n"
            "            role=role,\n"
            "            goal=duty,\n"
            '            backstory=f"You are the {role}. {duty}",\n'
            "            llm=llm,\n"
            "            tools=TOOLS,\n"
            "            verbose=False,\n"
            "        )\n"
            "        for role, duty in ROLES\n"
            "    ]\n"
            "    job = Task(\n"
            '        description=f"{INSTRUCTIONS}\\n\\nTask: {{task}}",\n'
            '        expected_output="One answer combining every specialist\'s contribution.",\n'
            "    )\n"
            "    return Crew(\n"
            "        agents=members,\n"
            "        tasks=[job],\n"
            "        process=Process.hierarchical,\n"
            "        manager_llm=llm,\n"
            "    )"
        )

    invoke = (
        "        del user_id\n"
        '        result = await self.runtime.kickoff_async(inputs={"task": task})\n'
        '        for task_output in getattr(result, "tasks_output", None) or []:\n'
        "            self._steps.append(\n"
        "                {\n"
        '                    "role": getattr(task_output, "agent", "") or "",\n'
        '                    "output": str(task_output),\n'
        "                }\n"
        "            )\n"
        "        return str(result).strip()"
    )
    stream = "        yield await self._invoke(task, user_id)"

    return {
        "imports": "\n".join(imports),
        "stdlib": [],
        "tools": tools,
        "model_body": model_body,
        "runtime_body": runtime_body,
        "init_extra": "",
        "invoke": invoke,
        "stream": stream,
    }


# --------------------------------------------------------------------------
# OpenAI Agents SDK
# --------------------------------------------------------------------------


def _openai_agents(provider: str, pattern: str, spec: dict) -> dict:
    topology = spec["topology"]
    wire = provider in OPENAI_WIRE

    imports = [
        "from agents import Agent as OAIAgent, ModelSettings, Runner, function_tool",
        "from agents import set_tracing_disabled",
    ]
    if wire:
        imports.append("from agents import OpenAIChatCompletionsModel")
        imports.append("from openai import AsyncOpenAI")
        model_body = (
            f'    """{PROVIDER_LABELS[provider]} speaks the OpenAI chat completions API, so the\n'
            "    SDK is pointed at it with a custom AsyncOpenAI client.\n"
            '    """\n'
            "    client = AsyncOpenAI(\n"
            '        api_key=config.provider.api_key or "not-needed",\n'
            "        base_url=config.provider.base_url or None,\n"
            "    )\n"
            "    return OpenAIChatCompletionsModel(model=config.provider.model, openai_client=client)"
        )
    else:
        imports.append("from agents.extensions.models.litellm_model import LitellmModel")
        prefix = LITELLM_PREFIXES[provider]
        model_body = (
            f'    """{PROVIDER_LABELS[provider]} is served through the SDK\'s LiteLLM extension."""\n'
            "    return LitellmModel(\n"
            f'        model=f"{prefix}/{{config.provider.model}}",\n'
            "        api_key=config.provider.api_key or None,\n"
            "    )"
        )

    tools = (
        "@function_tool\n"
        "def recall(query: str) -> str:\n"
        '    """Look up previously stored context for the current task."""\n'
        '    return f"no stored context for {query!r} yet"\n\n\n'
        "TOOLS = [recall]\n"
    )

    settings = (
        "    settings = ModelSettings(\n"
        "        temperature=config.provider.temperature,\n"
        "        max_tokens=config.provider.max_tokens,\n"
        "    )\n"
    )

    if topology == "single":
        runtime_body = (
            '    """One SDK agent; the Runner supplies the tool-calling loop."""\n'
            "    set_tracing_disabled(not config.telemetry.enabled)\n"
            + settings
            + "    return OAIAgent(\n"
            "        name=APP_NAME,\n"
            "        instructions=INSTRUCTIONS,\n"
            "        model=build_model(config),\n"
            "        model_settings=settings,\n"
            "        tools=TOOLS,\n"
            "    )"
        )
    elif topology in {"pipeline", "loop", "fanout"}:
        repeat = "ROUNDS" if topology == "loop" else "1"
        extra = ""
        if topology == "fanout":
            extra = (
                "    stages.append(\n"
                "        OAIAgent(\n"
                '            name="merge",\n'
                "            instructions=(\n"
                '                "Combine the branch answers into one coherent response. "\n'
                '                "Resolve disagreements explicitly."\n'
                "            ),\n"
                "            model=model,\n"
                "            model_settings=settings,\n"
                "        )\n"
                "    )\n"
            )
        runtime_body = (
            '    """One SDK agent per role, orchestrated by this module."""\n'
            "    set_tracing_disabled(not config.telemetry.enabled)\n"
            "    model = build_model(config)\n" + settings + "    stages = [\n"
            "        OAIAgent(\n"
            "            name=role,\n"
            '            instructions=f"{INSTRUCTIONS}\\n\\nYour role is {role}: {duty}",\n'
            "            model=model,\n"
            "            model_settings=settings,\n"
            "            tools=TOOLS,\n"
            "        )\n"
            f"        for _ in range({repeat})\n"
            "        for role, duty in ROLES\n"
            "    ]\n" + extra + "    return stages"
        )
    else:  # supervisor
        runtime_body = (
            '    """Specialists are registered as SDK handoffs from the supervisor agent."""\n'
            "    set_tracing_disabled(not config.telemetry.enabled)\n"
            "    model = build_model(config)\n" + settings + "    specialists = [\n"
            "        OAIAgent(\n"
            "            name=role,\n"
            "            handoff_description=duty,\n"
            '            instructions=f"You are the {role}. {duty}",\n'
            "            model=model,\n"
            "            model_settings=settings,\n"
            "            tools=TOOLS,\n"
            "        )\n"
            "        for role, duty in ROLES\n"
            "    ]\n"
            "    return OAIAgent(\n"
            "        name=APP_NAME,\n"
            "        instructions=INSTRUCTIONS,\n"
            "        model=model,\n"
            "        model_settings=settings,\n"
            "        handoffs=specialists,\n"
            "    )"
        )

    if topology in {"single", "supervisor"}:
        invoke = (
            "        del user_id\n"
            "        result = await Runner.run(self.runtime, task)\n"
            '        return str(result.final_output or "").strip()'
        )
        stream = (
            "        del user_id\n"
            "        streamed = Runner.run_streamed(self.runtime, task)\n"
            "        async for event in streamed.stream_events():\n"
            '            data = getattr(event, "data", None)\n'
            '            delta = getattr(data, "delta", None)\n'
            "            if delta:\n"
            "                yield str(delta)"
        )
    elif topology == "fanout":
        invoke = (
            "        del user_id\n"
            "        *branches, merger = self.runtime\n"
            "        results = await asyncio.gather(*(Runner.run(branch, task) for branch in branches))\n"
            "        for branch, result in zip(branches, results):\n"
            '            self._steps.append({"role": branch.name, "output": str(result.final_output)})\n'
            '        joined = "\\n\\n".join(f"[{b.name}]\\n{r.final_output}" for b, r in zip(branches, results))\n'
            '        merged = await Runner.run(merger, f"Task: {task}\\n\\nBranch answers:\\n{joined}")\n'
            '        return str(merged.final_output or "").strip()'
        )
        stream = "        yield await self._invoke(task, user_id)"
    else:
        invoke = (
            "        del user_id\n"
            "        carried = task\n"
            "        for stage in self.runtime:\n"
            "            result = await Runner.run(stage, carried)\n"
            '            carried = str(result.final_output or "")\n'
            '            self._steps.append({"role": stage.name, "output": carried})\n'
            "        return carried.strip()"
        )
        stream = "        yield await self._invoke(task, user_id)"

    stdlib = ["import asyncio"] if topology == "fanout" else []
    return {
        "imports": "\n".join(imports),
        "stdlib": stdlib,
        "tools": tools,
        "model_body": model_body,
        "runtime_body": runtime_body,
        "init_extra": "",
        "invoke": invoke,
        "stream": stream,
    }


# --------------------------------------------------------------------------
# Strands Agents
# --------------------------------------------------------------------------


def _strands(provider: str, pattern: str, spec: dict) -> dict:
    topology = spec["topology"]

    imports = ["from strands import Agent as StrandsAgent, tool"]
    if provider == "gemini":
        imports.append("from strands.models.gemini import GeminiModel")
        model_body = (
            '    """Native Strands binding for Gemini."""\n'
            "    return GeminiModel(\n"
            '        client_args={"api_key": config.provider.api_key},\n'
            "        model_id=config.provider.model,\n"
            "        params={\n"
            '            "temperature": config.provider.temperature,\n'
            '            "max_output_tokens": config.provider.max_tokens,\n'
            "        },\n"
            "    )"
        )
    elif provider == "anthropic":
        imports.append("from strands.models.anthropic import AnthropicModel")
        model_body = (
            '    """Native Strands binding for Anthropic."""\n'
            "    return AnthropicModel(\n"
            '        client_args={"api_key": config.provider.api_key},\n'
            "        model_id=config.provider.model,\n"
            "        max_tokens=config.provider.max_tokens,\n"
            '        params={"temperature": config.provider.temperature},\n'
            "    )"
        )
    elif provider == "ollama":
        imports.append("from strands.models.ollama import OllamaModel")
        model_body = (
            '    """Strands talks to a local Ollama daemon over its native API."""\n'
            "    return OllamaModel(\n"
            '        host=config.provider.base_url or "http://localhost:11434",\n'
            "        model_id=config.provider.model,\n"
            "        temperature=config.provider.temperature,\n"
            "    )"
        )
    else:
        imports.append("from strands.models.openai import OpenAIModel")
        model_body = (
            f'    """{PROVIDER_LABELS[provider]} is reached through the OpenAI-compatible API."""\n'
            "    return OpenAIModel(\n"
            "        client_args={\n"
            '            "api_key": config.provider.api_key or "not-needed",\n'
            '            "base_url": config.provider.base_url or None,\n'
            "        },\n"
            "        model_id=config.provider.model,\n"
            "        params={\n"
            '            "temperature": config.provider.temperature,\n'
            '            "max_tokens": config.provider.max_tokens,\n'
            "        },\n"
            "    )"
        )

    tools = (
        "@tool\n"
        "def recall(query: str) -> str:\n"
        '    """Look up previously stored context for the current task."""\n'
        '    return f"no stored context for {query!r} yet"\n\n\n'
        "TOOLS = [recall]\n"
    )

    if topology == "single":
        runtime_body = (
            '    """One Strands agent; the SDK owns the reasoning and tool loop."""\n'
            "    return StrandsAgent(\n"
            "        name=APP_NAME,\n"
            "        model=build_model(config),\n"
            "        system_prompt=INSTRUCTIONS,\n"
            "        tools=TOOLS,\n"
            "    )"
        )
    elif topology in {"pipeline", "loop", "fanout"}:
        repeat = "ROUNDS" if topology == "loop" else "1"
        extra = ""
        if topology == "fanout":
            extra = (
                "    stages.append(\n"
                "        StrandsAgent(\n"
                '            name="merge",\n'
                "            model=model,\n"
                "            system_prompt=(\n"
                '                "Combine the branch answers into one coherent response. "\n'
                '                "Resolve disagreements explicitly."\n'
                "            ),\n"
                "        )\n"
                "    )\n"
            )
        runtime_body = (
            '    """One Strands agent per role, orchestrated by this module."""\n'
            "    model = build_model(config)\n"
            "    stages = [\n"
            "        StrandsAgent(\n"
            "            name=role,\n"
            "            model=model,\n"
            '            system_prompt=f"{INSTRUCTIONS}\\n\\nYour role is {role}: {duty}",\n'
            "            tools=TOOLS,\n"
            "        )\n"
            f"        for _ in range({repeat})\n"
            "        for role, duty in ROLES\n"
            "    ]\n" + extra + "    return stages"
        )
    else:  # supervisor
        runtime_body = (
            '    """A supervisor agent plus specialist agents it delegates to."""\n'
            "    model = build_model(config)\n"
            '    roster = "\\n".join(f"- {r}: {d}" for r, d in ROLES)\n'
            "    supervisor = StrandsAgent(\n"
            "        name=APP_NAME,\n"
            "        model=model,\n"
            '        system_prompt=f"{INSTRUCTIONS}\\n\\nSpecialists:\\n{roster}",\n'
            "    )\n"
            "    specialists = [\n"
            "        StrandsAgent(\n"
            "            name=role,\n"
            "            model=model,\n"
            '            system_prompt=f"You are the {role}. {duty}",\n'
            "            tools=TOOLS,\n"
            "        )\n"
            "        for role, duty in ROLES\n"
            "    ]\n"
            "    return supervisor, specialists"
        )

    if topology == "single":
        invoke = (
            "        del user_id\n"
            "        result = await self.runtime.invoke_async(task)\n"
            "        return str(result).strip()"
        )
        stream = (
            "        del user_id\n"
            "        async for event in self.runtime.stream_async(task):\n"
            '            chunk = event.get("data") if isinstance(event, dict) else None\n'
            "            if chunk:\n"
            "                yield str(chunk)"
        )
    elif topology == "fanout":
        invoke = (
            "        del user_id\n"
            "        *branches, merger = self.runtime\n"
            "        results = await asyncio.gather(*(branch.invoke_async(task) for branch in branches))\n"
            "        for branch, result in zip(branches, results):\n"
            '            self._steps.append({"role": branch.name, "output": str(result)})\n'
            '        joined = "\\n\\n".join(f"[{b.name}]\\n{r}" for b, r in zip(branches, results))\n'
            '        merged = await merger.invoke_async(f"Task: {task}\\n\\nBranch answers:\\n{joined}")\n'
            "        return str(merged).strip()"
        )
        stream = "        yield await self._invoke(task, user_id)"
    elif topology == "supervisor":
        invoke = (
            "        del user_id\n"
            "        supervisor, specialists = self.runtime\n"
            "        brief = str(await supervisor.invoke_async(task))\n"
            '        self._steps.append({"role": supervisor.name, "output": brief})\n'
            "        parts = [brief]\n"
            "        for specialist in specialists:\n"
            '            brief_task = f"Task: {task}\\n\\nSupervisor brief:\\n{brief}"\n'
            "            text = str(await specialist.invoke_async(brief_task))\n"
            '            self._steps.append({"role": specialist.name, "output": text})\n'
            '            parts.append(f"[{specialist.name}]\\n{text}")\n'
            '        return "\\n\\n".join(parts).strip()'
        )
        stream = "        yield await self._invoke(task, user_id)"
    else:
        invoke = (
            "        del user_id\n"
            "        carried = task\n"
            "        for stage in self.runtime:\n"
            "            carried = str(await stage.invoke_async(carried))\n"
            '            self._steps.append({"role": stage.name, "output": carried})\n'
            "        return carried.strip()"
        )
        stream = "        yield await self._invoke(task, user_id)"

    stdlib = ["import asyncio"] if topology == "fanout" else []
    return {
        "imports": "\n".join(imports),
        "stdlib": stdlib,
        "tools": tools,
        "model_body": model_body,
        "runtime_body": runtime_body,
        "init_extra": "",
        "invoke": invoke,
        "stream": stream,
    }


FRAMEWORK_RENDERERS = {
    "google-adk": _adk,
    "langgraph": _langgraph,
    "langchain": _langchain,
    "crewai": _crewai,
    "openai-agents": _openai_agents,
    "strands": _strands,
}


_MODULE = '''"""Root agent for __NAME__.

Provider:      __PROVIDER_LABEL__ (__PROVIDER__)
Orchestration: __FRAMEWORK_LABEL__ (__FRAMEWORK__)
Pattern:       __PATTERN__ (__TOPOLOGY__ topology)

Generated module. It uses the __FRAMEWORK_LABEL__ SDK directly:

* ``build_model``   binds __PROVIDER_LABEL__ to __FRAMEWORK_LABEL__.
* ``build_runtime`` assembles the __PATTERN__ topology from __FRAMEWORK_LABEL__ primitives.
* ``Agent``         adapts that runtime to the application-facing interface.

Edit the instructions, tools and topology here — this is the one file that owns
the agent's behaviour.
"""

from __future__ import annotations

__STDLIB__import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

__IMPORTS__

from app.agentic.config import AgentConfig
from app.agentic.memory import MemoryEntry, create_memory
from app.agentic.telemetry import Tracer

PROVIDER = "__PROVIDER__"
FRAMEWORK = "__FRAMEWORK__"
PATTERN = "__PATTERN__"
APP_NAME = "__NAME__"

__INSTRUCTIONS__

__CONSTANTS__

__TOOLS__

def build_model(config: AgentConfig) -> Any:
__MODEL_BODY__


def build_runtime(config: AgentConfig) -> Any:
__RUNTIME_BODY__


@dataclass(slots=True)
class AgentResult:
    """Outcome of a single agent run."""

    final_output: str = ""
    steps: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0


class Agent:
    """__FRAMEWORK_LABEL__ agent exposed through a framework-agnostic interface."""

    def __init__(self, config: AgentConfig, runtime: Any) -> None:
        self.config = config
        self.runtime = runtime
        self.memory = create_memory(config.memory)
        self.tracer = Tracer(config.telemetry)
        self._steps: list[dict[str, Any]] = []__INIT_EXTRA__

    @classmethod
    def from_config(cls, name: str | None = None, config: AgentConfig | None = None) -> "Agent":
        """Build the agent from environment-backed configuration."""
        config = config or AgentConfig.from_env(name=name or APP_NAME)
        return cls(config, build_runtime(config))

    async def run(self, task: str, user_id: str = "system") -> AgentResult:
        """Run the __PATTERN__ topology once and return the structured result."""
        started = time.perf_counter()
        self._steps = []
        async with self.tracer.span(
            "agent.run", {"framework": FRAMEWORK, "pattern": PATTERN, "provider": PROVIDER}
        ):
            output = await self._invoke(task, user_id)
        await self._remember(task, output)
        return AgentResult(
            final_output=output,
            steps=list(self._steps),
            duration_ms=(time.perf_counter() - started) * 1000,
        )

    async def stream(self, task: str, user_id: str = "system") -> AsyncIterator[str]:
        """Yield output chunks as the topology produces them."""
        async for chunk in self._stream(task, user_id):
            yield chunk

    async def chat(self, message: str) -> str:
        """Convenience wrapper that returns only the final text."""
        return (await self.run(message)).final_output

    async def _invoke(self, task: str, user_id: str) -> str:
__INVOKE__

    async def _stream(self, task: str, user_id: str) -> AsyncIterator[str]:
__STREAM__

    async def _remember(self, task: str, output: str) -> None:
        await self.memory.add(MemoryEntry(role="user", content=task))
        await self.memory.add(MemoryEntry(role="assistant", content=output))


root_agent = Agent.from_config(APP_NAME)
'''


_INIT = '''"""Agent package for __NAME__.

Re-exports the generated agent so ``from app.agentic.agent import Agent`` keeps
working regardless of how ``agent.py`` is structured internally.
"""

from app.agentic.agent.agent import (
    FRAMEWORK,
    PATTERN,
    PROVIDER,
    Agent,
    AgentResult,
    build_model,
    build_runtime,
    root_agent,
)

__all__ = [
    "FRAMEWORK",
    "PATTERN",
    "PROVIDER",
    "Agent",
    "AgentResult",
    "build_model",
    "build_runtime",
    "root_agent",
]
'''


def render_agent_package(name: str, provider: str, framework: str, pattern: str) -> dict[str, str]:
    """Render ``agent/__init__.py`` and ``agent/agent.py`` for one selection."""
    if provider not in PROVIDER_LABELS:
        raise ValueError(f"unknown provider: {provider}")
    if framework not in FRAMEWORK_RENDERERS:
        raise ValueError(f"unknown framework: {framework}")
    if pattern not in PATTERN_SPECS:
        raise ValueError(f"unknown pattern: {pattern}")

    spec = PATTERN_SPECS[pattern]
    parts = FRAMEWORK_RENDERERS[framework](provider, pattern, spec)

    constants = _roles_constant(spec)
    if "rounds" in spec:
        constants += f"ROUNDS = {spec['rounds']}\n"

    stdlib = "".join(f"{line}\n" for line in parts["stdlib"])
    init_extra = f"\n{parts['init_extra']}" if parts["init_extra"] else ""

    tokens = {
        "__NAME__": name,
        "__PROVIDER__": provider,
        "__PROVIDER_LABEL__": PROVIDER_LABELS[provider],
        "__FRAMEWORK__": framework,
        "__FRAMEWORK_LABEL__": FRAMEWORK_LABELS[framework],
        "__PATTERN__": pattern,
        "__TOPOLOGY__": spec["topology"],
        "__STDLIB__": stdlib,
        "__IMPORTS__": parts["imports"],
        "__INSTRUCTIONS__": _instructions_literal(spec["instruction"]),
        "__CONSTANTS__": constants,
        "__TOOLS__": parts["tools"],
        "__MODEL_BODY__": parts["model_body"],
        "__RUNTIME_BODY__": parts["runtime_body"],
        "__INIT_EXTRA__": init_extra,
        "__INVOKE__": parts["invoke"],
        "__STREAM__": parts["stream"],
    }

    module = _MODULE
    for token, value in tokens.items():
        module = module.replace(token, value)

    # Collapse the blank lines left behind by empty slots.
    while "\n\n\n\n" in module:
        module = module.replace("\n\n\n\n", "\n\n\n")

    return {
        "__init__.py": _INIT.replace("__NAME__", name),
        "agent.py": module,
    }
