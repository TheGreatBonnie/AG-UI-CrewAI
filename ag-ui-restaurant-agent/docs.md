<!-- CopilotKit Hooks -->

<!-- useCopilotAction Hook -->

useCopilotAction
The useCopilotAction hook allows your copilot to take action in the app.

useCopilotAction is a React hook that you can use in your application to provide custom actions that can be called by the AI. Essentially, it allows the Copilot to execute these actions contextually during a chat, based on the user’s interactions and needs.

Here's how it works:

Use useCopilotAction to set up actions that the Copilot can call. To provide more context to the Copilot, you can provide it with a description (for example to explain what the action does, under which conditions it can be called, etc.).

Then you define the parameters of the action, which can be simple, e.g. primitives like strings or numbers, or complex, e.g. objects or arrays.

Finally, you provide a handler function that receives the parameters and returns a result. CopilotKit takes care of automatically inferring the parameter types, so you get type safety and autocompletion for free.

To render a custom UI for the action, you can provide a render() function. This function lets you render a custom component or return a string to display.

Usage
Simple Usage

useCopilotAction({
name: "sayHello",
description: "Say hello to someone.",
parameters: [
{
name: "name",
type: "string",
description: "name of the person to say greet",
},
],
handler: async ({ name }) => {
alert(`Hello, ${name}!`);
},
});
Generative UI
This hooks enables you to dynamically generate UI elements and render them in the copilot chat. For more information, check out the Generative UI page.

Parameters
action
Action
required
The function made available to the Copilot. See Action.

name
string
required
The name of the action.

handler
(args) => Promise<any>
required
The handler of the action.

description
string
A description of the action. This is used to instruct the Copilot on how to use the action.

available
'enabled' | 'disabled' | 'remote'
Use this property to control when the action is available to the Copilot. When set to "remote", the action is available only for remote agents.

followUp
boolean
Default: "true"
Whether to report the result of a function call to the LLM which will then provide a follow-up response. Pass false to disable

parameters
Parameter[]
The parameters of the action. See Parameter.

name
string
required
The name of the parameter.

type
string
required
The type of the argument. One of:

"string"
"number"
"boolean"
"object"
"object[]"
"string[]"
"number[]"
"boolean[]"
description
string
A description of the argument. This is used to instruct the Copilot on what this argument is used for.

enum
string[]
For string arguments, you can provide an array of possible values.

required
boolean
Whether or not the argument is required. Defaults to true.

attributes
If the argument is of a complex type, i.e. object or object[], this field lets you define the attributes of the object. For example:

{
name: "addresses",
description: "The addresses extracted from the text.",
type: "object[]",
attributes: [
{
name: "street",
type: "string",
description: "The street of the address.",
},
{
name: "city",
type: "string",
description: "The city of the address.",
},
// ...
],
}
render
string | (props: ActionRenderProps<T>) => string
Render lets you define a custom component or string to render instead of the default. You can either pass in a string or a function that takes the following props:

status
'inProgress' | 'executing' | 'complete'
"inProgress": arguments are dynamically streamed to the function, allowing you to adjust your UI in real-time.
"executing": The action handler is executing.
"complete": The action handler has completed execution.
args
T
The arguments passed to the action in real time. When the status is "inProgress", they are possibly incomplete.

result
any
The result returned by the action. It is only available when the status is "complete".

renderAndWaitForResponse
(props: ActionRenderPropsWait<T>) => React.ReactElement
This is similar to render, but provides a respond function in the props that you must call with the user's response. The component will remain rendered until respond is called. The response will be passed as the result to the action handler.

status
'inProgress' | 'executing' | 'complete'
"inProgress": arguments are dynamically streamed to the function, allowing you to adjust your UI in real-time.
"executing": The action handler is executing.
"complete": The action handler has completed execution.
args
T
The arguments passed to the action in real time. When the status is "inProgress", they are possibly incomplete.

respond
(result: any) => void
A function that must be called with the user's response. The response will be passed as the result to the action handler. Only available when status is "executing".

result
any
The result returned by the action. It is only available when the status is "complete".

dependencies
any[]
An optional array of dependencies.

<!-- Generative UI -->

Generative UI
Learn how to embed custom UI components in the chat window.

Render custom components in the chat UI
When a user interacts with your Copilot, you may want to render a custom UI component. useCopilotAction allows to give the LLM the option to render your custom component through the render property.

Render a component
Fetch data & render
renderAndWaitForResponse (HITL)
Render strings
Catch all renders
The renderAndWaitForResponse method allows for returning values asynchronously from the render function.

This is great for Human-in-the-Loop flows, where the AI assistant can prompt the end-user with a choice (rendered inside the chat UI), and the user can make the choice by pressing a button in the chat UI.

"use client" // only necessary if you are using Next.js with the App Router.
import { useCopilotAction } from "@copilotkit/react-core";

useCopilotAction({
name: "handleMeeting",
description: "Handle a meeting by booking or canceling",
parameters: [
{
name: "meeting",
type: "string",
description: "The meeting to handle",
required: true,
},
{
name: "date",
type: "string",
description: "The date of the meeting",
required: true,
},
{
name: "title",
type: "string",
description: "The title of the meeting",
required: true,
},
],
renderAndWaitForResponse: ({ args, respond, status }) => {
const { meeting, date, title } = args;
return (
<MeetingConfirmationDialog
meeting={meeting}
date={date}
title={title}
onConfirm={() => respond?.('meeting confirmed')}
onCancel={() => respond?.('meeting canceled')}
/>
);
},
});
What do the different status states mean?
Why do I need "use client" in Next.js with the App Router?
Test it out!
After defining the action with a render method, ask the copilot to perform the task. For example, you can now ask the copilot to "show tasks" and see the custom UI component rendered in the chat interface.

<!-- useCoAgentStateRender Hook -->

useCoAgentStateRender
The useCoAgentStateRender hook allows you to render the state of the agent in the chat.

The useCoAgentStateRender hook allows you to render UI or text based components on a Agentic Copilot's state in the chat. This is particularly useful for showing intermediate state or progress during Agentic Copilot operations.

Usage
Simple Usage

import { useCoAgentStateRender } from "@copilotkit/react-core";

type YourAgentState = {
agent_state_property: string;
}

useCoAgentStateRender<YourAgentState>({
name: "basic_agent",
nodeName: "optionally_specify_a_specific_node",
render: ({ status, state, nodeName }) => {
return (
<YourComponent
        agentStateProperty={state.agent_state_property}
        status={status}
        nodeName={nodeName}
      />
);
},
});
This allows for you to render UI components or text based on what is happening within the agent.

Example
A great example of this is in our Perplexity Clone where we render the progress of an agent's internet search as it is happening. You can play around with it below or learn how to build it with its demo.

This example is hosted on Vercel and may take a few seconds to load.

Parameters
name
string
required
The name of the coagent.

nodeName
string
The node name of the coagent.

handler
(props: CoAgentStateRenderHandlerArguments<T>) => void | Promise<void>
The handler function to handle the state of the agent.

render
| ((props: CoAgentStateRenderProps<T>) => string | React.ReactElement | undefined | null) | string
The render function to handle the state of the agent.

<!-- useCoAgent Hook -->

useCoAgent
The useCoAgent hook allows you to share state bidirectionally between your application and the agent.

Usage of this hook assumes some additional setup in your application, for more information on that see the CoAgents getting started guide.

CoAgents demonstration
This hook is used to integrate an agent into your application. With its use, you can render and update the state of an agent, allowing for a dynamic and interactive experience. We call these shared state experiences agentic copilots, or CoAgents for short.

Usage
Simple Usage

import { useCoAgent } from "@copilotkit/react-core";

type AgentState = {
count: number;
}

const agent = useCoAgent<AgentState>({
name: "my-agent",
initialState: {
count: 0,
},
});

useCoAgent returns an object with the following properties:

const {
name, // The name of the agent currently being used.
nodeName, // The name of the current LangGraph node.
state, // The current state of the agent.
setState, // A function to update the state of the agent.
running, // A boolean indicating if the agent is currently running.
start, // A function to start the agent.
stop, // A function to stop the agent.
run, // A function to re-run the agent. Takes a HintFunction to inform the agent why it is being re-run.
} = agent;
Finally we can leverage these properties to create reactive experiences with the agent!

const { state, setState } = useCoAgent<AgentState>({
name: "my-agent",
initialState: {
count: 0,
},
});

return (

  <div>
    <p>Count: {state.count}</p>
    <button onClick={() => setState({ count: state.count + 1 })}>Increment</button>
  </div>
);
This reactivity is bidirectional, meaning that changes to the state from the agent will be reflected in the UI and vice versa.

Parameters
options
UseCoagentOptions<T>
required
The options to use when creating the coagent.

name
string
required
The name of the agent to use.

initialState
T | any
The initial state of the agent.

state
T | any
State to manage externally if you are using this hook with external state management.

setState
(newState: T | ((prevState: T | undefined) => T)) => void
A function to update the state of the agent if you are using this hook with external state management.

<!-- Curl Command -->

curl -X POST http://localhost:8000/agent \
 -H "Content-Type: application/json" \
 -d '{
"thread_id": "test_thread_123",
"run_id": "test_run_456",
"messages": [
{
"id": "msg_1",
"role": "user",
"content": "Find restaurants in New York City"
}
],
"tools": [],
"context": [],
"forwarded_props": {},
"state": {}
}'
