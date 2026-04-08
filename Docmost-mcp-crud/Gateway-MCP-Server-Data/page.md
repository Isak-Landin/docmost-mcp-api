# Gateway and MCP Tool Server — Data Responsibilities

_Source: MCP specification (modelcontextprotocol.io), April 2026._

This document maps the data each node owns, the data each node sends to the other, and
the combined data a gateway must assemble from all connected MCP servers in order to
present a model with everything it needs to use tools across all of them.

---

## The three nodes (and the one we ignore here)

| Node | Role |
|---|---|
| **MCP Server** | Owns and exposes tools, resources, and prompt templates |
| **MCP Client** | Lives inside the gateway. One client instance per connected MCP server. Speaks the protocol. |
| **Gateway (MCP Host)** | Manages all clients, aggregates data from all servers, assembles model input |
| ~~LLM~~ | ~~End consumer of assembled data — out of scope for this mapping~~ |

A gateway creates one MCP client per connected server. The gateway is the only node that
sees the full picture across all servers simultaneously.

---

## Phase 1 — Connection: what the gateway stores per server

When the gateway connects to an MCP server it sends an `initialize` request and receives
a response. From that exchange it must store the following per-server record:

### Data sent by the gateway to the server (initialize request)

| Field | Purpose |
|---|---|
| `protocolVersion` | Version the gateway wants to speak |
| `clientInfo.name` | Gateway identity (name, version) |
| `capabilities` | Which client-side features the gateway supports (sampling, elicitation, roots) |

### Data the server returns (initialize response)

| Field | What the gateway must store |
|---|---|
| `protocolVersion` | Confirmed version — gateway must use this for all further messages |
| `serverInfo.name` | Display name of this server |
| `serverInfo.version` | Server version |
| `serverInfo.description` | Human-readable description of the server |
| `capabilities.tools` | Whether this server has tools; whether it will notify on list changes |
| `capabilities.resources` | Whether this server has resources; subscribe/listChanged flags |
| `capabilities.prompts` | Whether this server has prompts; listChanged flag |
| `capabilities.logging` | Whether server emits log messages |
| `instructions` | Optional free-text instructions the server publishes for the model |

The gateway must store this per-server block for every connected server before doing
anything else. Nothing else in the connection is valid until the `initialized`
notification has been sent back by the gateway to confirm readiness.

---

## Phase 2 — Discovery: what the gateway fetches from each server

After initialization, the gateway calls the list methods for each capability the server
declared. The data returned must be collected and stored per server.

### Tools (`tools/list`)

The server returns a list of tool definitions. For each tool the gateway stores:

| Field | Description |
|---|---|
| `name` | Unique identifier for the tool (scoped to this server) |
| `title` | Optional human-readable display name |
| `description` | What the tool does — used to help the model decide when to call it |
| `inputSchema` | JSON Schema object defining required and optional input parameters |
| `outputSchema` | Optional JSON Schema defining the output structure |
| `annotations` | Optional hints (e.g. destructive, read-only, audience) |

The gateway must track which server owns each tool, because `tools/call` must be routed
to the correct server.

### Resources (`resources/list`)

The server returns a list of resource definitions. For each resource the gateway stores:

| Field | Description |
|---|---|
| `uri` | Unique identifier (e.g. `file:///path`, custom scheme) |
| `name` | Short identifier |
| `title` | Optional display name |
| `description` | What this data represents |
| `mimeType` | Content type |
| `annotations.audience` | Whether aimed at `user`, `assistant`, or both |
| `annotations.priority` | 0.0–1.0 importance hint |

Resource _content_ (the actual text or binary data) is only fetched via `resources/read`
when needed — not at discovery time.

### Prompts (`prompts/list`)

The server returns a list of prompt templates. For each prompt the gateway stores:

| Field | Description |
|---|---|
| `name` | Unique identifier |
| `title` | Optional display name |
| `description` | What this prompt template does |
| `arguments` | List of named arguments (name, description, required flag) |

Prompt _content_ (the actual messages) is only fetched via `prompts/get` when a specific
prompt is invoked — not at discovery time.

---

## Phase 3 — Assembly: what the gateway combines before prompting the model

When a user request arrives, the gateway must assemble a complete context payload from
the data it has collected across all connected servers. This is the gateway's primary
internal responsibility.

### 1. Aggregated tool list (across all servers)

All tool definitions from all servers, merged into a single flat list. Each entry is the
tool's `name`, `description`, and `inputSchema`. This gives the model a complete view of
every callable action available to it.

The gateway must ensure tool names are unique across servers. If two servers expose a
tool with the same name, the gateway must disambiguate (e.g. by prefixing with server
name) before presenting to the model.

### 2. Server instructions (aggregated)

Each server may return an `instructions` string in its initialize response. The gateway
should collect all non-empty instruction strings from all connected servers and include
them in the system context. These describe how each server expects to be used.

### 3. Resource content (selective)

Resources are not automatically included. The gateway selects which resources are relevant
to the current request (by audience annotation, priority, or explicit user selection) and
fetches their content via `resources/read`. The returned text or binary content is then
included in the context alongside the user message.

### 4. Prompt messages (on demand)

If a specific prompt template is invoked, the gateway calls `prompts/get` with any
required arguments. The server returns a list of `PromptMessage` objects (role + content).
The gateway appends these messages into the conversation before the user message.

### 5. The combined payload the gateway sends to the model

Assembled from all of the above:

| Component | Source |
|---|---|
| System instructions | Merged `instructions` strings from all server initialize responses |
| Tool definitions | Aggregated `tools/list` results from all servers |
| Resource content | Fetched `resources/read` content for selected resources |
| Prompt messages | `prompts/get` messages if a prompt was invoked |
| Conversation history | Prior turns managed by the gateway |
| User message | The current user input |

The model receives this complete payload and can reference any tool from any server by
name. When it decides to call a tool, it returns a tool call with the tool's `name` and
`arguments`. The gateway routes that call to the server that owns the tool.

---

## Phase 4 — Tool call routing: data flow on execution

When the model returns a tool call:

1. Gateway receives: `{ name: "tool_name", arguments: { ... } }`
2. Gateway looks up which server owns `tool_name`
3. Gateway sends `tools/call` to that server: `{ name, arguments }`
4. Server executes and returns a result with `content` (text, image, resource link, or embedded resource) and an `isError` flag
5. Gateway appends the result to the conversation as a tool result message
6. Gateway sends the updated conversation back to the model for the next turn

---

## What the gateway must persist per registered MCP server

To allow dynamic addition of new MCP servers (without hardcoding), the gateway needs to
store the following registration record for each server:

| Field | Description |
|---|---|
| Connection endpoint | URL (Streamable HTTP) or command + args (stdio) |
| Transport type | `http` or `stdio` |
| Auth data | Bearer token, API key, or other credential (for HTTP transport) |
| Server name | From `serverInfo.name` after initialization |
| Protocol version | Confirmed during initialization |
| Declared capabilities | `tools`, `resources`, `prompts`, `logging` flags |
| Server instructions | `instructions` string from initialize response |
| Tool registry | All tool definitions fetched via `tools/list` |
| Resource registry | All resource definitions fetched via `resources/list` |
| Prompt registry | All prompt definitions fetched via `prompts/list` |

Adding a new server means: store the connection endpoint + auth, run the initialize
handshake, fetch the list data, and merge the new tools/resources/prompts into the
gateway's aggregate view. No hardcoding is needed — the protocol itself provides all
the data through standard discovery methods.

---

## Real-time updates: how the gateway keeps its data current

If a server declared `listChanged: true` for tools, resources, or prompts, it will send
notifications when its lists change:

| Notification | Meaning |
|---|---|
| `notifications/tools/list_changed` | Re-fetch `tools/list` from this server and update aggregate |
| `notifications/resources/list_changed` | Re-fetch `resources/list` from this server |
| `notifications/prompts/list_changed` | Re-fetch `prompts/list` from this server |
| `notifications/resources/updated` | Re-fetch `resources/read` for the changed URI |

The gateway handles these notifications per-server and updates only the affected server's
slice of the aggregate — other servers are unaffected.
