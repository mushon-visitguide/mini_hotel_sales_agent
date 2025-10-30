# Gemini CLI Architecture Overview

## Core Components

### 1. **CoderAgentExecutor** (`packages/a2a-server/src/agent/executor.ts`)
The main orchestrator that manages the entire agent lifecycle.

**Key Responsibilities:**
- Creates and manages Task instances
- Handles task state (submitted, in-progress, completed, failed, canceled)
- Manages execution loop with abort signals
- Persists task state to TaskStore

### 2. **Task** (`packages/a2a-server/src/agent/task.ts`)
Manages individual conversation sessions and execution state.

**Key Responsibilities:**
- Maintains conversation history
- Manages tool call lifecycle (pending → execution → completion)
- Coordinates between user messages, LLM, and tool execution
- Publishes events to EventBus

### 3. **ToolRegistry** (`packages/core/src/tools/tool-registry.ts`)
Central registry for all available tools.

**Key Responsibilities:**
- Registers built-in tools (file ops, shell, web search, etc.)
- Discovers tools from MCP servers
- Discovers custom tools via command line
- Provides tool schemas to LLM as FunctionDeclarations

### 4. **GeminiClient** (`packages/core/src/core/geminiChat.ts`)
Handles communication with Gemini LLM API.

**Key Responsibilities:**
- Sends conversation history + tools to Gemini
- Streams LLM responses
- Validates response content
- Handles retries and fallback models

### 5. **CoreToolScheduler** (`packages/core/src/core/coreToolScheduler.ts`)
Executes tool calls returned by the LLM.

**Key Responsibilities:**
- Schedules tool execution (parallel or sequential)
- Handles tool confirmations/approvals
- Collects tool results
- Reports tool status updates

---

## Execution Flow

### When User Sends a Task:

```
1. User Message
   ↓
2. CoderAgentExecutor.execute()
   ↓
3. Task.acceptUserMessage()
   ↓
4. GeminiClient.sendMessage() → [LLM CALL #1]
   - Input: conversation history + user message + available tools
   - Output: text response + tool calls
   ↓
5. Task.scheduleToolCalls()
   ↓
6. CoreToolScheduler executes tools in parallel/batch
   - read_file, write_file, shell, etc.
   ↓
7. Task.sendCompletedToolsToLlm() → [LLM CALL #2]
   - Input: conversation history + tool results
   - Output: text response (+ possibly more tool calls)
   ↓
8. Repeat steps 5-7 until no more tool calls
   ↓
9. Set task state to "input-required" (waiting for user)
```

---

## Key Design Patterns

### 1. **LLM Call Strategy**
- **NOT called for every tool**: LLM is called once per "turn"
- LLM decides which tools to call upfront
- All tools execute in batch
- Results sent back to LLM in single call
- Loop continues until LLM stops calling tools

### 2. **Tool Execution**
- Tools are executed via subprocess/function calls
- Built-in tools: file ops (read, write, edit, glob, grep), shell, web fetch/search
- MCP tools: discovered from MCP servers (Model Context Protocol)
- Custom tools: discovered via command-line tool discovery command

### 3. **Agentic Loop**
```
User Input → LLM → Tool Calls → Execute Tools → LLM → [repeat] → Final Response
```

The loop continues until:
- LLM produces no tool calls (task complete)
- User cancels
- Error occurs

---

## Tool System

### Built-in Tools
Located in `packages/core/src/tools/`:
- **read-file.ts**: Read file contents
- **write-file.ts**: Write new files
- **edit.ts**: Edit existing files
- **grep.ts / ripGrep.ts**: Search file contents
- **glob.ts**: Find files by pattern
- **shell.ts**: Execute shell commands
- **web-fetch.ts**: Fetch web content
- **web-search.ts**: Google search integration

### Tool Discovery
1. **Built-in tools**: Registered at startup
2. **MCP tools**: Discovered via MCP protocol from configured servers
3. **Custom tools**: Discovered via `toolDiscoveryCommand` (returns JSON array of FunctionDeclarations)

### Tool Call Flow
```typescript
// 1. LLM returns tool calls
toolCalls: [
  { name: "read_file", params: { file_path: "/path/to/file" } },
  { name: "shell", params: { command: "npm test" } }
]

// 2. Scheduler executes all tools
results = await scheduler.executeTools(toolCalls)

// 3. Results sent back to LLM
LLM receives: "read_file result: ..., shell result: ..."

// 4. LLM generates response or more tool calls
```

---

## State Management

### Task States
- `submitted`: New task created
- `in-progress`: LLM processing or tools executing
- `input-required`: Waiting for user input
- `completed`: Task finished successfully
- `failed`: Error occurred
- `canceled`: User canceled

### Conversation History
Maintained as `Content[]` array:
```typescript
[
  { role: "user", parts: [{ text: "..." }] },
  { role: "model", parts: [{ functionCall: {...} }] },
  { role: "user", parts: [{ functionResponse: {...} }] },
  { role: "model", parts: [{ text: "..." }] }
]
```

---

## Configuration

### Config Object (`packages/core/src/config/config.ts`)
Central configuration includes:
- Model selection (gemini-2.5-pro, gemini-2.5-flash, etc.)
- Tool registry
- MCP server configurations
- Workspace context
- Authentication settings

### Settings Files
- `~/.gemini/settings.json`: Global user settings
- `.gemini/settings.json`: Per-project settings
- `GEMINI.md`: Project-specific context/instructions

---

## Key Differences from Your Implementation

| Aspect | Gemini CLI | Your Implementation |
|--------|-----------|---------------------|
| **LLM Calls** | One call per turn, tools batched | ? |
| **Tool Execution** | Parallel via scheduler | ? |
| **State Management** | Stateful tasks with persistence | ? |
| **Tool Discovery** | Dynamic (MCP + command-line) | Static registration? |
| **Conversation** | Full history maintained | ? |

---

## Summary

**Core Flow:**
1. User sends message
2. **LLM Call #1**: Analyzes request → returns tool calls
3. Execute all tools in parallel
4. **LLM Call #2**: Processes tool results → generates response (or more tool calls)
5. Repeat until complete

**Key Points:**
- ✅ LLM is NOT called for every tool individually
- ✅ Tools are batched and executed in parallel
- ✅ LLM decides tool usage upfront based on available FunctionDeclarations
- ✅ Extensible via MCP protocol for custom tools
- ✅ Stateful conversation with full history
