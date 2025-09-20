import sys
sys.setrecursionlimit(2000)
import tkinter as tk
from tkinter import scrolledtext, messagebox
import asyncio
import threading
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState
from typing import Annotated, List, Dict, Any, AsyncIterator
import operator
import queue

class AsyncioThread(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.loop = asyncio.new_event_loop()

    def run(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def run_coro_from_main_thread(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    def stop(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

class MCPInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("MCP Agent Interface")
        self.root.geometry("800x600")
        
        self.model = ChatOllama(model="qwen2.5:7b")
        self.agent = None
        self.session = None
        
        self.asyncio_thread = AsyncioThread()
        self.asyncio_thread.start()
        
        self.setup_ui()
        self.setup_mcp()
        
    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        output_label = tk.Label(main_frame, text="Agent Chain of Thought & Responses:", anchor="w")
        output_label.pack(fill=tk.X, pady=(0, 5))
        
        self.output_text = scrolledtext.ScrolledText(
            main_frame, 
            height=20, 
            state=tk.DISABLED,
            wrap=tk.WORD,
            bg="#f0f0f0"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        input_frame = tk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        input_label = tk.Label(input_frame, text="Enter command:")
        input_label.pack(anchor="w")
        
        self.input_text = tk.Text(input_frame, height=3, wrap=tk.WORD)
        self.input_text.pack(fill=tk.X, pady=(5, 0))
        self.input_text.bind('<Control-Return>', self.on_send)
        
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        self.send_button = tk.Button(
            button_frame, 
            text="Send Command (Ctrl+Enter)", 
            command=self.on_send,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold")
        )
        self.send_button.pack(side=tk.LEFT, padx=(0, 10))
        
        clear_button = tk.Button(
            button_frame, 
            text="Clear Output", 
            command=self.clear_output,
            bg="#f44336",
            fg="white"
        )
        clear_button.pack(side=tk.LEFT)
        
        self.status_label = tk.Label(
            main_frame, 
            text="Status: Initializing MCP connection...", 
            fg="orange"
        )
        self.status_label.pack(fill=tk.X, pady=(10, 0))
        
    def setup_mcp(self):
        def init_mcp():
            try:
                self.asyncio_thread.run_coro_from_main_thread(self.init_mcp_async())
                self.root.after(0, lambda: self.status_label.config(
                    text="Status: Connected to MCP server", fg="green"
                ))
            except Exception as e:
                stre = str(e)
                self.root.after(0, lambda: self.status_label.config(
                    text=f"Status: Error - {stre}", fg="red"
                ))
        
        init_thread = threading.Thread(target=init_mcp, daemon=True)
        init_thread.start()
        
    async def init_mcp_async(self):
        server_params = StdioServerParameters(
            command="python",
            args=["pygui.py"],
        )
        
        self.client = stdio_client(server_params)
        read, write = await self.client.__aenter__()
        self.session_cm = ClientSession(read, write)
        self.session = await self.session_cm.__aenter__()
        await self.session.initialize()
        
        tools = await load_mcp_tools(self.session)
        self.agent = create_react_agent(self.model, tools)
        
    def cleanup(self):
        if self.agent:
            self.asyncio_thread.run_coro_from_main_thread(self.cleanup_mcp_async())
        self.asyncio_thread.stop()

    async def cleanup_mcp_async(self):
        if self.session_cm:
            await self.session_cm.__aexit__(None, None, None)
        if self.client:
            await self.client.__aexit__(None, None, None)
        
    def append_to_output(self, text, tag=None):
        self.output_text.config(state=tk.NORMAL)
        if tag:
            self.output_text.insert(tk.END, f"[{tag}] ")
        self.output_text.insert(tk.END, text + "\n")
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
        
    def clear_output(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)
        
    def on_send(self, event=None):
        command = self.input_text.get("1.0", tk.END).strip()
        if not command:
            return
            
        if self.agent is None:
            messagebox.showwarning("Not Ready", "MCP agent is not initialized yet. Please wait.")
            return
            
        self.input_text.delete("1.0", tk.END)
        self.append_to_output(f"You: {command}", "USER")
        self.send_button.config(state=tk.DISABLED, text="Processing...")
        
        def process_command():
            try:
                result = self.asyncio_thread.run_coro_from_main_thread(self.send_command_async(command))
                self.root.after(0, lambda: self.display_result(result))
            except Exception as e:
                error_msg = f"Error processing command: {str(e)}"
                self.root.after(0, lambda: self.append_to_output(error_msg, "ERROR"))
            finally:
                self.root.after(0, lambda: self.send_button.config(
                    state=tk.NORMAL, text="Send Command (Ctrl+Enter)"
                ))
        
        thread = threading.Thread(target=process_command, daemon=True)
        thread.start()
        
    async def send_command_async(self, command):
        config = {}
        
        # Set recursion limit in config
        config["recursion_limit"] = 50
        msg = {"messages": [{"role": "user", "content": command}]}

        initial_state = ChainOfThoughtState(
            messages=[HumanMessage(content=command)],
            reasoning_steps=[],
            current_step=0
        )
        result = await self.agent.ainvoke(initial_state,config)
        return result
        
    def display_result(self, result):
        self.append_to_output("Agent Response:", "AGENT")
        
        if 'messages' in result and isinstance(result['messages'], list):
            # Skip the first message, which is the user's input.
            for message in result['messages'][1:]:
                role = "Message"
                if hasattr(message, 'type'):
                    role = message.type.capitalize()

                output = f"[{role}]"
                
                content = None
                if hasattr(message, 'content') and message.content is not None:
                    content = message.content
                elif hasattr(message, 'message') and message.message is not None:
                    content = message.message

                if content is not None:
                    if isinstance(content, str):
                        output += f"\n{content}"
                    else:
                        # For non-string content (like tool results), pretty-print.
                        try:
                            import json
                            output += f"\n{json.dumps(content, indent=2)}"
                        except (TypeError, ImportError):
                            output += f"\n{str(content)}"

                if hasattr(message, 'tool_calls') and message.tool_calls:
                    calls = []
                    for call in message.tool_calls:
                        name = "unknown_tool"
                        args = "{}"
                        if isinstance(call, dict):
                            name = call.get('name', name)
                            args = str(call.get('args', {}))
                        elif hasattr(call, 'name') and hasattr(call, 'args'):
                            name = call.name
                            args = str(call.args)
                        calls.append(f"{name}({args})")
                    output += f"\nTool Calls: {', '.join(calls)}"

                # If after all that we only have the role, use the default str representation
                if output == f"[{role}]":
                    output = f"[{role}] {str(message)}"

                self.append_to_output(output)
        else:
            self.append_to_output(f"  {str(result)}")
            
        self.append_to_output("-" * 50)

# Enhanced State for Chain of Thought
class ChainOfThoughtState(MessagesState):
    """Enhanced state that tracks reasoning steps"""
    reasoning_steps: Annotated[List[str], operator.add] = []
    current_step: int = 0
    max_reasoning_steps: int = 10
    start_time: float = 0.0

def main():
    root = tk.Tk()
    app = MCPInterface(root)
    
    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            app.cleanup()
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()